"""
BTTS Model — predicts both teams to score (Yes/No).
Target variable: 1 = yes, 0 = no.
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

MODEL_PATH = os.path.join(os.path.dirname(__file__), "saved", "btts_model.pkl")
MARKET = "btts"

FEATURE_COLS = [
    "home_btts_pct", "away_btts_pct", "btts_combined",
    "home_xg", "away_xg", "home_xga", "away_xga",
    "home_ppg", "away_ppg"
]


def load_training_data() -> pd.DataFrame:
    """Pull historical completed fixtures and join with team stats."""
    result = supabase.table("wc_fixtures").select("*").eq("match_completed", True).execute()
    fixtures = result.data

    if len(fixtures) < 20:
        print(f"  [BTTS Model] Insufficient database training data ({len(fixtures)} matches). Generating synthetic training data...")
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
            "home_btts_pct": home_stats.get("btts_pct", 50.0),
            "away_btts_pct": away_stats.get("btts_pct", 50.0),
            "btts_combined": (home_stats.get("btts_pct", 50.0) + away_stats.get("btts_pct", 50.0)) / 2,
            "home_xg": home_stats.get("xg", 1.2),
            "away_xg": away_stats.get("xg", 1.2),
            "home_xga": home_stats.get("xga", 1.2),
            "away_xga": away_stats.get("xga", 1.2),
            "home_ppg": home_stats.get("ppg", 1.5),
            "away_ppg": away_stats.get("ppg", 1.5),
            "result_btts": f.get("result_btts", False)
        })

    return pd.DataFrame(records)


def generate_synthetic_data() -> pd.DataFrame:
    """Generate mock historical games with realistic BTTS outcomes."""
    records = []
    np.random.seed(42)

    for i in range(100):
        h_btts = np.random.uniform(35.0, 65.0)
        a_btts = np.random.uniform(40.0, 60.0)
        comb_btts = (h_btts + a_btts) / 2
        
        # Simulate outcomes: probability of both scoring is roughly 50%
        # but correlates with xG and btts_combined
        h_xg = np.random.uniform(0.9, 2.2)
        a_xg = np.random.uniform(0.8, 1.9)
        h_xga = np.random.uniform(0.8, 2.0)
        a_xga = np.random.uniform(0.9, 2.1)
        
        prob_btts = (comb_btts / 100.0) * 0.7 + (h_xg + a_xg) * 0.1
        prob_btts = min(0.85, max(0.15, prob_btts))
        actual = np.random.binomial(1, prob_btts)

        records.append({
            "home_btts_pct": h_btts,
            "away_btts_pct": a_btts,
            "btts_combined": comb_btts,
            "home_xg": h_xg,
            "away_xg": a_xg,
            "home_xga": h_xga,
            "away_xga": a_xga,
            "home_ppg": np.random.uniform(0.5, 2.5),
            "away_ppg": np.random.uniform(0.5, 2.5),
            "result_btts": bool(actual)
        })

    return pd.DataFrame(records)


def build_target(df: pd.DataFrame) -> pd.Series:
    """1 if both teams scored, else 0."""
    return df["result_btts"].astype(int)


def train():
    """Train the BTTS model and save to disk."""
    print(f"Training BTTS model...")
    df = load_training_data()

    X = df[FEATURE_COLS].fillna(0)
    y = build_target(df)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    base_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model = CalibratedClassifierCV(base_model, cv=3, method="isotonic")
    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)[:, 1]
    ll = log_loss(y_test, probs, labels=[0, 1])
    bs = brier_score_loss(y_test, probs)
    print(f"  Log-loss: {ll:.4f} | Brier: {bs:.4f}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"  Model saved to {MODEL_PATH}")

    # Log model run to Supabase
    try:
        supabase.table("model_runs").insert({
            "model_name": "btts_v1",
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
            print(f"  [BTTS Model] Error loading model pkl: {e}. Using rule-based fallback.")
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
        "prediction": "yes" if prob >= 0.5 else "no",
        "probability": round(float(prob), 4),
        "confidence_tier": tier,
        "model_version": "btts_v1",
    }


def calculate_fallback_prob(features: pd.DataFrame) -> float:
    """Fallback rule: average of btts combined percentage with an adjustments for xG."""
    try:
        comb_btts = features["btts_combined"].values[0]
        # Normalize: convert percentage to decimal. 
        # Adjust slightly for expected goals
        prob = (comb_btts / 100.0)
        h_xg = features["home_xg"].values[0]
        a_xg = features["away_xg"].values[0]
        prob += (h_xg + a_xg - 2.4) * 0.05
        return min(0.85, max(0.15, prob))
    except Exception:
        return 0.5


if __name__ == "__main__":
    train()
