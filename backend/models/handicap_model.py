"""
Handicap Model — predicts home team covers -0.5 Asian Handicap.
Target variable: 1 = home covers (home win, i.e. "over"), 0 = fails to cover (draw/away win, i.e. "under").
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

MODEL_PATH = os.path.join(os.path.dirname(__file__), "saved", "handicap_model.pkl")
MARKET = "handicap"

FEATURE_COLS = [
    "home_ppg", "away_ppg", "home_xg", "away_xg",
    "home_xga", "away_xga", "home_sentiment", "away_sentiment",
    "sentiment_delta"
]


def load_training_data() -> pd.DataFrame:
    """Pull historical completed fixtures and join with team stats."""
    result = supabase.table("wc_fixtures").select("*").eq("match_completed", True).execute()
    fixtures = result.data

    if len(fixtures) < 20:
        print(f"  [Handicap Model] Insufficient database training data ({len(fixtures)} matches). Generating synthetic training data...")
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
            "home_ppg": home_stats.get("ppg", 1.5),
            "away_ppg": away_stats.get("ppg", 1.5),
            "home_xg": home_stats.get("xg", 1.2),
            "away_xg": away_stats.get("xg", 1.2),
            "home_xga": home_stats.get("xga", 1.2),
            "away_xga": away_stats.get("xga", 1.2),
            "home_sentiment": home_stats.get("sentiment_score", 0.0),
            "away_sentiment": away_stats.get("sentiment_score", 0.0),
            "sentiment_delta": home_stats.get("sentiment_score", 0.0) - away_stats.get("sentiment_score", 0.0),
            "result_home_goals": f.get("result_home_goals", 0),
            "result_away_goals": f.get("result_away_goals", 0)
        })

    return pd.DataFrame(records)


def generate_synthetic_data() -> pd.DataFrame:
    """Generate mock historical games with realistic handicap cover outcomes."""
    records = []
    np.random.seed(42)

    for i in range(100):
        h_ppg = np.random.uniform(0.5, 2.5)
        a_ppg = np.random.uniform(0.5, 2.5)
        h_xg = np.random.uniform(0.8, 2.2)
        a_xg = np.random.uniform(0.8, 2.0)
        h_xga = np.random.uniform(0.8, 2.0)
        a_xga = np.random.uniform(0.8, 2.1)
        h_sent = np.random.uniform(-0.3, 0.4)
        a_sent = np.random.uniform(-0.3, 0.4)
        sent_delta = h_sent - a_sent
        
        # Simulate outcome: home team covers if home win. 
        # Cover probability increases with ppg difference and xg difference
        cover_prob = 0.45 + (h_ppg - a_ppg) * 0.12 + (h_xg - a_xg) * 0.1 + sent_delta * 0.1
        cover_prob = min(0.85, max(0.15, cover_prob))
        actual = np.random.binomial(1, cover_prob)

        # Generate mock scores that match the cover outcome
        if actual == 1:
            # Home wins
            h_goals = np.random.randint(1, 4)
            a_goals = np.random.randint(0, h_goals)
        else:
            # Draw or Away wins
            a_goals = np.random.randint(0, 3)
            h_goals = np.random.randint(0, a_goals + 1)

        records.append({
            "home_ppg": h_ppg,
            "away_ppg": a_ppg,
            "home_xg": h_xg,
            "away_xg": a_xg,
            "home_xga": h_xga,
            "away_xga": a_xga,
            "home_sentiment": h_sent,
            "away_sentiment": a_sent,
            "sentiment_delta": sent_delta,
            "result_home_goals": h_goals,
            "result_away_goals": a_goals
        })

    return pd.DataFrame(records)


def build_target(df: pd.DataFrame) -> pd.Series:
    """1 if home wins, else 0."""
    return (df["result_home_goals"] > df["result_away_goals"]).astype(int)


def train():
    """Train the handicap model and save to disk."""
    print(f"Training handicap model...")
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
            "model_name": "handicap_v1",
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
            print(f"  [Handicap Model] Error loading model pkl: {e}. Using rule-based fallback.")
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
        "model_version": "handicap_v1",
    }


def calculate_fallback_prob(features: pd.DataFrame) -> float:
    """Fallback rule: compare PPG and sentiment scores."""
    try:
        h_ppg = features["home_ppg"].values[0]
        a_ppg = features["away_ppg"].values[0]
        sent_delta = features["sentiment_delta"].values[0]
        
        prob = 0.45 + (h_ppg - a_ppg) * 0.1 + sent_delta * 0.1
        return min(0.85, max(0.15, prob))
    except Exception:
        return 0.5


if __name__ == "__main__":
    train()
