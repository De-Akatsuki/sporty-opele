"""
Master pipeline script.
Run this daily (or before each matchday) to:
1. Scrape latest team stats from FootyStats
2. Update sentiment scores from Reddit
3. Build features for today's fixtures
4. Run all 5 models
5. Push predictions to Supabase

Usage:
    python backend/pipeline/run_pipeline.py
"""

import sys
import os
from datetime import date

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scraper.footystats_scraper import scrape_and_push
from scraper.reddit_sentiment import get_team_sentiment
from features.feature_engineering import build_match_features, run_feature_pipeline_all
from db.supabase_client import supabase, insert_prediction

import models.corners_model as corners
import models.cards_model as cards
import models.btts_model as btts
import models.handicap_model as handicap
import models.goals_model as goals


def update_sentiments():
    """Fetch all teams and update their sentiment scores."""
    print("Updating sentiment scores...")
    try:
        teams = supabase.table("wc_teams").select("team_name").execute().data
    except Exception as e:
        print(f"Error fetching teams for sentiment: {e}")
        return

    if not teams:
        print("No teams found in database to update sentiment.")
        return

    for team in teams:
        name = team["team_name"]
        score = get_team_sentiment(name)
        try:
            supabase.table("wc_teams").update(
                {"sentiment_score": score}
            ).eq("team_name", name).execute()
            print(f"  {name}: {score:+.4f}")
        except Exception as e:
            print(f"  ✗ Failed to update sentiment for {name}: {e}")


def run_predictions():
    """For today's fixtures, run all models and push predictions."""
    today = date.today().isoformat()
    print(f"\nRunning predictions for {today}...")

    try:
        fixtures = supabase.table("wc_fixtures").select("*").eq(
            "match_date", today
        ).eq("match_completed", False).execute().data
    except Exception as e:
        print(f"Error querying fixtures: {e}")
        fixtures = []

    if not fixtures:
        print("No fixtures today. Checking for ANY uncompleted fixtures in the database to populate predictions...")
        try:
            fixtures = supabase.table("wc_fixtures").select("*").eq("match_completed", False).execute().data
        except Exception as e:
            print(f"Error querying uncompleted fixtures: {e}")
            fixtures = []

    if not fixtures:
        print("No uncompleted fixtures found in the database. Please seed fixtures first.")
        return

    model_runners = [corners, cards, btts, handicap, goals]

    # Clean existing predictions for these fixtures to prevent primary key/duplicate errors
    fixture_ids = [f["id"] for f in fixtures]
    for fid in fixture_ids:
        try:
            supabase.table("predictions").delete().eq("fixture_id", fid).execute()
        except Exception:
            pass

    for fixture in fixtures:
        home = fixture["home_team"]
        away = fixture["away_team"]
        fixture_id = fixture["id"]
        match_date = fixture["match_date"]
        print(f"\n  {home} vs {away} (Fixture ID: {fixture_id}, Date: {match_date})")

        try:
            features = build_match_features(home, away, fixture_id=fixture_id)
        except ValueError as e:
            print(f"  Skipping: {e}")
            continue

        for model in model_runners:
            try:
                result = model.predict(features)
                result["fixture_id"] = fixture_id
                # Handle possible DataFrame to float conversions safely
                sentiment_val = features["home_sentiment"].values[0]
                result["sentiment_signal"] = float(sentiment_val)
                insert_prediction(result)
                print(f"    [{result['market']}] {result['prediction']} @ {result['probability']} ({result['confidence_tier']})")
            except Exception as e:
                print(f"    ✗ Error predicting {model.MARKET}: {e}")


def main():
    print("=" * 50)
    print("SPORTY-OPELE PIPELINE")
    print("=" * 50)

    print("\n[1/5] Scraping FootyStats & Seeding Teams...")
    scrape_and_push()

    print("\n[2/5] Updating sentiment...")
    update_sentiments()

    print("\n[3/5] Engineering features (processed_features)...")
    run_feature_pipeline_all()

    print("\n[4/5] Running predictions...")
    run_predictions()

    print("\n[5/5] Done. Check Supabase for latest predictions.")


if __name__ == "__main__":
    main()
