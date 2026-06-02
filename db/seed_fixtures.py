"""
Seeds the database with WC 2026 Teams (via footystats_scraper mock generator),
completed historical World Cup fixtures (for training), and upcoming fixtures.
"""

import os
import sys
import random
from datetime import date, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from db.supabase_client import supabase
from scraper.footystats_scraper import generate_mock_teams, upsert_team

# Historical matches (Home, Away, Home Goals, Away Goals, Home Corners, Away Corners, Total Cards, BTTS)
HISTORICAL_MATCHES = [
    ("Argentina", "France", 3, 3, 6, 5, 4, True),
    ("Croatia", "Morocco", 2, 1, 4, 3, 5, True),
    ("France", "Morocco", 2, 0, 5, 3, 3, False),
    ("Argentina", "Croatia", 3, 0, 4, 4, 3, False),
    ("England", "France", 1, 2, 5, 2, 4, True),
    ("Morocco", "Portugal", 1, 0, 3, 7, 5, False),
    ("Netherlands", "Argentina", 2, 2, 2, 6, 8, True),
    ("Croatia", "Brazil", 1, 1, 3, 5, 4, True),
    ("Japan", "Croatia", 1, 1, 4, 5, 2, True),
    ("Brazil", "South Korea", 4, 1, 6, 4, 1, True),
    ("England", "Senegal", 3, 0, 4, 3, 0, False),
    ("France", "Poland", 3, 1, 8, 1, 3, True),
    ("Argentina", "Australia", 2, 1, 4, 3, 4, True),
    ("Netherlands", "USA", 3, 1, 4, 5, 2, True),
    ("Cameroon", "Brazil", 1, 0, 3, 8, 4, False),
    ("Poland", "Argentina", 0, 2, 1, 9, 5, False),
    ("Saudi Arabia", "Mexico", 1, 2, 2, 5, 7, True),
    ("Tunisia", "France", 1, 0, 7, 4, 1, False),
    ("Australia", "Denmark", 1, 0, 2, 4, 3, False),
    ("Iran", "USA", 0, 1, 1, 5, 4, False),
    ("Wales", "England", 0, 3, 2, 6, 2, False),
    ("Ecuador", "Senegal", 1, 2, 3, 6, 4, True),
    ("Netherlands", "Qatar", 2, 0, 4, 2, 1, False),
    ("Costa Rica", "Germany", 2, 4, 2, 8, 1, True),
    ("Japan", "Spain", 2, 1, 0, 2, 3, True),
    ("Croatia", "Belgium", 0, 0, 2, 4, 2, False),
    ("Canada", "Morocco", 1, 2, 4, 2, 4, True),
    ("Germany", "Japan", 1, 2, 6, 2, 0, True),
    ("Spain", "Costa Rica", 7, 0, 5, 0, 2, False),
    ("Argentina", "Saudi Arabia", 1, 2, 9, 2, 6, True)
]

# Upcoming fixtures: (Home, Away, Days From Today, Stage, Group)
UPCOMING_MATCHES = [
    ("USA", "England", 0, "Group Stage", "Group B"),
    ("Brazil", "France", 0, "Group Stage", "Group A"),
    ("Argentina", "Germany", 1, "Group Stage", "Group C"),
    ("Spain", "Italy", 1, "Group Stage", "Group D"),
    ("Japan", "Netherlands", 2, "Group Stage", "Group E"),
    ("Mexico", "Portugal", 2, "Group Stage", "Group F")
]


def seed():
    print("=" * 50)
    print("SEEDING DATABASE FIXTURES")
    print("=" * 50)

    # 1. Seed teams
    df_teams = generate_mock_teams()
    print(f"\nSeeding {len(df_teams)} teams into wc_teams...")
    for _, row in df_teams.iterrows():
        upsert_team(row.to_dict())
    print("  ✓ Teams seeded.")

    # 2. Seed historical fixtures
    print(f"\nSeeding {len(HISTORICAL_MATCHES)} historical matches...")
    # Delete existing fixtures first to prevent duplicate errors
    try:
        supabase.table("wc_fixtures").delete().execute()
        print("  Cleared existing fixtures.")
    except Exception:
        pass

    today = date.today()
    for idx, m in enumerate(HISTORICAL_MATCHES):
        home, away, hg, ag, hc, ac, cards, btts = m
        match_date = (today - timedelta(days=30 - idx)).isoformat()
        
        fixture_data = {
            "id": idx + 1,
            "match_date": match_date,
            "kickoff_time": "18:00:00",
            "home_team": home,
            "away_team": away,
            "stage": "Historical",
            "group_name": "N/A",
            "venue": "Historical Stadium",
            "city": "Qatar",
            "result_home_goals": hg,
            "result_away_goals": ag,
            "result_home_corners": hc,
            "result_away_corners": ac,
            "result_total_cards": cards,
            "result_btts": btts,
            "match_completed": True
        }
        try:
            supabase.table("wc_fixtures").insert(fixture_data).execute()
        except Exception as e:
            print(f"  ✗ Failed to insert historical fixture {home} vs {away}: {e}")

    print("  ✓ Historical fixtures seeded.")

    # 3. Seed upcoming fixtures
    print(f"\nSeeding {len(UPCOMING_MATCHES)} upcoming fixtures...")
    start_id = len(HISTORICAL_MATCHES) + 1
    for idx, m in enumerate(UPCOMING_MATCHES):
        home, away, days_offset, stage, group = m
        match_date = (today + timedelta(days=days_offset)).isoformat()
        
        fixture_data = {
            "id": start_id + idx,
            "match_date": match_date,
            "kickoff_time": "20:00:00",
            "home_team": home,
            "away_team": away,
            "stage": stage,
            "group_name": group,
            "venue": "MetLife Stadium" if idx % 2 == 0 else "Azteca Stadium",
            "city": "New York" if idx % 2 == 0 else "Mexico City",
            "match_completed": False
        }
        try:
            supabase.table("wc_fixtures").insert(fixture_data).execute()
            print(f"  + {home} vs {away} scheduled for {match_date}")
        except Exception as e:
            print(f"  ✗ Failed to insert upcoming fixture {home} vs {away}: {e}")

    print("\nDatabase seeding completed successfully!")


if __name__ == "__main__":
    seed()
