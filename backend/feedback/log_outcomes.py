"""
After a match completes, call this script to log actual outcomes.
It compares predictions against real results and updates prediction_outcomes.

Usage:
    python backend/feedback/log_outcomes.py --fixture_id 12
"""

import argparse
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.supabase_client import supabase, log_outcome


def process_fixture(fixture_id: int):
    """Read completed fixture, compare to predictions, log outcomes."""
    try:
        fixture = supabase.table("wc_fixtures").select("*").eq("id", fixture_id).execute().data
    except Exception as e:
        print(f"Error querying fixture {fixture_id}: {e}")
        return

    if not fixture:
        print(f"Fixture {fixture_id} not found.")
        return

    f = fixture[0]
    try:
        predictions = supabase.table("predictions").select("*").eq(
            "fixture_id", fixture_id
        ).execute().data
    except Exception as e:
        print(f"Error querying predictions for fixture {fixture_id}: {e}")
        return

    total_corners = (f.get("result_home_corners") or 0) + (f.get("result_away_corners") or 0)
    total_cards = f.get("result_total_cards") or 0
    btts = f.get("result_btts")
    total_goals = (f.get("result_home_goals") or 0) + (f.get("result_away_goals") or 0)

    # handicap covers -0.5 if home team win (over), otherwise fails to cover (under)
    actual_map = {
        "corners": "over" if total_corners > 9.5 else "under",
        "cards": "over" if total_cards > 3.5 else "under",
        "btts": "yes" if btts else "no",
        "goals": "over" if total_goals > 2.5 else "under",
        "handicap": "over" if (f.get("result_home_goals") or 0) > (f.get("result_away_goals") or 0) else "under",
    }

    # Remove existing outcomes for this fixture to prevent unique constraint failures
    try:
        supabase.table("prediction_outcomes").delete().eq("fixture_id", fixture_id).execute()
    except Exception:
        pass

    for pred in predictions:
        market = pred["market"]
        actual = actual_map.get(market)
        if not actual:
            continue

        correct = pred["prediction"] == actual
        try:
            log_outcome({
                "prediction_id": pred["id"],
                "fixture_id": fixture_id,
                "market": market,
                "prediction": pred["prediction"],
                "probability": pred["probability"],
                "actual_outcome": actual,
                "correct": correct,
            })
            status = "✓" if correct else "✗"
            print(f"  [{market}] predicted={pred['prediction']} actual={actual} {status}")
        except Exception as e:
            print(f"  ✗ Failed to log outcome for {market}: {e}")

    # Mark fixture as completed
    try:
        supabase.table("wc_fixtures").update(
            {"match_completed": True}
        ).eq("id", fixture_id).execute()
        print(f"\nFixture {fixture_id} marked as completed.")
    except Exception as e:
        print(f"Failed to mark fixture {fixture_id} as completed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture_id", type=int, required=True)
    args = parser.parse_args()
    process_fixture(args.fixture_id)
