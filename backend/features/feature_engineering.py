"""
Builds the feature matrix for ML models.
One row per match, one column per feature.
"""

import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.supabase_client import supabase


def get_team_features(team_name: str) -> dict:
    """Fetch a team's stats from Supabase and return as feature dict."""
    result = supabase.table("wc_teams").select("*").eq("team_name", team_name).execute()
    if not result.data:
        return {}
    row = result.data[0]
    return {
        "ppg": row.get("ppg", 0) or 0.0,
        "xg": row.get("xg", 0) or 0.0,
        "xga": row.get("xga", 0) or 0.0,
        "btts_pct": row.get("btts_pct", 0) or 0.0,
        "clean_sheet_pct": row.get("clean_sheet_pct", 0) or 0.0,
        "avg_corners": row.get("avg_corners", 0) or 0.0,
        "avg_cards": row.get("avg_cards", 0) or 0.0,
        "avg_goals": row.get("avg_goals", 0) or 0.0,
        "over_25_pct": row.get("over_25_pct", 0) or 0.0,
        "sentiment_score": row.get("sentiment_score", 0) or 0.0,
    }


def build_match_features(home_team: str, away_team: str) -> pd.DataFrame:
    """
    Combine home + away team features into a single match feature row.
    Returns a single-row DataFrame ready for model.predict().
    """
    home = get_team_features(home_team)
    away = get_team_features(away_team)

    if not home or not away:
        raise ValueError(f"Missing team data for {home_team} or {away_team}")

    features = {
        # Home team features
        "home_ppg": home["ppg"],
        "home_xg": home["xg"],
        "home_xga": home["xga"],
        "home_btts_pct": home["btts_pct"],
        "home_clean_sheet_pct": home["clean_sheet_pct"],
        "home_avg_corners": home["avg_corners"],
        "home_avg_cards": home["avg_cards"],
        "home_avg_goals": home["avg_goals"],
        "home_over_25_pct": home["over_25_pct"],
        "home_sentiment": home["sentiment_score"],

        # Away team features
        "away_ppg": away["ppg"],
        "away_xg": away["xg"],
        "away_xga": away["xga"],
        "away_btts_pct": away["btts_pct"],
        "away_clean_sheet_pct": away["clean_sheet_pct"],
        "away_avg_corners": away["avg_corners"],
        "away_avg_cards": away["avg_cards"],
        "away_avg_goals": away["avg_goals"],
        "away_over_25_pct": away["over_25_pct"],
        "away_sentiment": away["sentiment_score"],

        # Combined features
        "total_avg_corners": home["avg_corners"] + away["avg_corners"],
        "total_avg_cards": home["avg_cards"] + away["avg_cards"],
        "total_avg_goals": home["avg_goals"] + away["avg_goals"],
        "btts_combined": (home["btts_pct"] + away["btts_pct"]) / 2,
        "sentiment_delta": home["sentiment_score"] - away["sentiment_score"],
    }

    return pd.DataFrame([features])
