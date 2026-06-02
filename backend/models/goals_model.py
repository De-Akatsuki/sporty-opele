"""
Goals Model — predicts total goals over/under 2.5.
Target variable: 1 = over 2.5 goals, 0 = under 2.5 goals.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss, brier_score_loss
import joblib
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.supabase_client import supabase

MODEL_PATH = os.path.join(os.path.dirname(__file__), "saved", "goals_model.pkl")
THRESHOLD = 2.5
MARKET = "goals"

FEATURE_COLS = [
    "home_avg_goals", "away_avg_goals", "total_avg_goals",
    "home_over_25_pct", "away_over_25_pct", "home_xg", "away_xg",
    "home_xga", "away_xga"
]


def load_training_data() -> pd.DataFrame:
    """Pull historical completed fixtures and join with team stats."""
    result = supabase.table("wc_fixtures").select("*").eq("match_completed", True).execute()
    fixtures = result.data

    if len(fixtures) < 20:
        print(f"  [Goals Model] Insufficient database training data ({len(fixtures)} matches). Generating synthetic training data...")
        return generate_synthetic_data()

    # Query all teams for feature mapping
    teams_result = supabase.table("wc_teams").select("*").execute()
    teams_map = {t["team_name"]: t for t in teams_result.data}

    records = []
    for f in fixtures:
        home_stats = teams_map.get(f["home_team"], {})
        away_stats = teams_map.get(f["away_team"], {})

        if not home_stats or not away_stats:
            continue

        records.append({
            "home_avg_goals": home_stats.get("avg_goals", 2.5),
            "away_avg_goals": away_stats.get("avg_goals", 2.5),
            "total_avg_goals": home_stats.get("avg_goals", 2.5) + away_stats.get("avg_goals", 2.5),
            "home_over_25_pct": home_stats.get("over_25_pct", 50.0),
            "away_over_25_pct": away_stats.get("over_25_pct", 50.0),
            "home_xg": home_stats.get("xg", 1.2),
            "away_xg": away_stats.get("xg", 1.2),
            "home_xga": home_stats.get("xga", 1.2),
            "away_xga": away_stats.get("xga", 1.2),
            "result_home_goals": f.get("result_home_goals", 1),
            "result_away_goals": f.get("result_away_goals", 1)
        })

    return pd.DataFrame(records)


def generate_synthetic_data() -> pd.DataFrame:
    """Generate mock historical games with realistic goals statistics."""
    records = []
    np.random.seed(42)

    for i in range(100):
        h_avg = np.random.uniform(1.0, 2.0)
        a_avg = np.random.uniform(0.9, 1.8)
        tot_avg = h_avg + a_avg
        
        # Simulate goals scored via poisson
        h_goals = np.random.poisson(h_avg)
        a_goals = np.random.poisson(a_avg)

        records.append({
            "home_avg_goals": h_avg,
            "away_avg_goals": a_avg,
            "total_avg_goals": tot_avg,
            "home_over_25_pct": np.random.uniform(35.0, 65.0),
            "away_over_25_pct": np.random.uniform(30.0, 60.0),
            "home_xg": h_avg,
            "away_xg": a_avg,
            "home_xga": np.random.uniform(0.9, 1.9),
            "away_xga": np.random.uniform(0.9, 1.9),
            "result_home_goals": h_goals,
            "result_away_goals": a_goals
        })

    return pd.DataFrame(records)


def build_target(df: pd.DataFrame) -> pd.Series:
    """1 if total goals > 2.5, else 0."""
    total = df["result_home_goals"] + df["result_away_goals"]
    return (total > THRESHOLD).astype(int)


def train():
    """Train the goals model and save to disk."""
    print(f"Training goals model (threshold: {THRESHOLD})...")
    df = load_training_data()

    X = df[FEATURE_COLS].fillna(0)
    y = build_target(df)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    base_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model = CalibratedClassifierCV(base_model, cv=3, method="isotonic")
    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)[:, 1]
    ll = log_loss(y_test, probs)
    bs = brier_score_loss(y_test, probs)
    print(f"  Log-loss: {ll:.4f} | Brier: {bs:.4f}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"  Model saved to {MODEL_PATH}")

    # Log model run to Supabase
    try:
        supabase.table("model_runs").insert({
            "model_name": "goals_v1",
            "market": MARKET,
            "accuracy": float(np.mean((probs >= 0.5) == y_test)),
            "log_loss": float(ll),
            "brier_score": float(bs),
            "training_samples": len(df)
        }).execute()
        print("  ✓ Logged run to Supabase")
    except Exception as e:
        print(f"  ✗ Failed to log model run: {e}")


def predict(features: pd.DataFrame) -> dict:
    """Load model and predict for a given match."""
    prob = 0.5
    
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            X = features[FEATURE_COLS].fillna(0)
            prob = model.predict_proba(X)[0][1]
        except Exception as e:
            print(f"  [Goals Model] Error loading model pkl: {e}. Using rule-based fallback.")
            prob = calculate_fallback_prob(features)
    else:
        prob = calculate_fallback_prob(features)

    # Confidence tier
    if prob >= 0.65 or prob <= 0.35:
        tier = "High"
    elif prob >= 0.55 or prob <= 0.45:
        tier = "Medium"
    else:
        tier = "Low"

    return {
        "market": MARKET,
        "prediction": "over" if prob >= 0.5 else "under",
        "probability": round(float(prob), 4),
        "confidence_tier": tier,
        "model_version": "goals_v1",
    }


def calculate_fallback_prob(features: pd.DataFrame) -> float:
    """Fallback rule: total avg goals vs average threshold of 2.5."""
    try:
        total_avg_goals = features["total_avg_goals"].values[0]
        # Normalize: average goals count is ~2.5. 
        # Map total goals from [1.5, 3.5] to prob [0.3, 0.7]
        prob = 0.5 + (total_avg_goals - 2.5) * 0.15
        return min(0.85, max(0.15, prob))
    except Exception:
        return 0.5


if __name__ == "__main__":
    train()
