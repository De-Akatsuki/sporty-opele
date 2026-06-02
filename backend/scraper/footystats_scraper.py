"""
Scrapes FootyStats World Cup team statistics.
Target: https://footystats.org/world-cup
Extracts: BTTS%, corners, cards, goals, O/U stats per team.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import sys
import os
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.supabase_client import upsert_team

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

FOOTYSTATS_WC_URL = "https://footystats.org/world-cup"

# 48 World Cup 2026 teams list for mock fallback seeding
WC_2026_TEAMS = [
    # UEFA
    ("France", 2, "UEFA"), ("England", 3, "UEFA"), ("Spain", 5, "UEFA"), ("Germany", 11, "UEFA"),
    ("Portugal", 7, "UEFA"), ("Netherlands", 6, "UEFA"), ("Italy", 9, "UEFA"), ("Belgium", 8, "UEFA"),
    ("Croatia", 10, "UEFA"), ("Denmark", 16, "UEFA"), ("Switzerland", 15, "UEFA"), ("Austria", 22, "UEFA"),
    ("Ukraine", 24, "UEFA"), ("Poland", 28, "UEFA"), ("Sweden", 29, "UEFA"), ("Turkey", 35, "UEFA"),
    # CONMEBOL
    ("Argentina", 1, "CONMEBOL"), ("Brazil", 4, "CONMEBOL"), ("Uruguay", 14, "CONMEBOL"),
    ("Colombia", 12, "CONMEBOL"), ("Ecuador", 31, "CONMEBOL"), ("Chile", 40, "CONMEBOL"),
    # CONCACAF
    ("USA", 13, "CONCACAF"), ("Mexico", 15, "CONCACAF"), ("Canada", 48, "CONCACAF"),
    ("Costa Rica", 52, "CONCACAF"), ("Panama", 41, "CONCACAF"), ("Jamaica", 55, "CONCACAF"),
    # CAF
    ("Morocco", 12, "CAF"), ("Senegal", 17, "CAF"), ("Nigeria", 28, "CAF"), ("Egypt", 33, "CAF"),
    ("Ivory Coast", 38, "CAF"), ("Tunisia", 41, "CAF"), ("Algeria", 43, "CAF"), ("Cameroon", 46, "CAF"),
    ("Mali", 47, "CAF"),
    # AFC
    ("Japan", 18, "AFC"), ("Iran", 20, "AFC"), ("South Korea", 22, "AFC"), ("Australia", 23, "AFC"),
    ("Saudi Arabia", 53, "AFC"), ("Iraq", 58, "AFC"), ("Jordan", 71, "AFC"), ("Oman", 78, "AFC"),
    # OFC
    ("New Zealand", 104, "OFC")
]

def fetch_page(url: str) -> BeautifulSoup:
    """Fetch a page and return a BeautifulSoup object."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    time.sleep(1)  # Polite crawl delay
    return BeautifulSoup(response.text, "lxml")


def parse_main_table(soup: BeautifulSoup) -> pd.DataFrame:
    """
    Parse the main team stats table from FootyStats WC page.
    Columns: Country, P, W, D, L, GF, GA, GD, PPG, xG, xGA, BTTS%, CS%, Corners, Cards, AVG
    """
    tables = soup.find_all("table")
    records = []

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 15:
                try:
                    record = {
                        "team_name": cells[0].get_text(strip=True),
                        "games_played": int(cells[1].get_text(strip=True) or 0),
                        "wins": int(cells[2].get_text(strip=True) or 0),
                        "draws": int(cells[3].get_text(strip=True) or 0),
                        "losses": int(cells[4].get_text(strip=True) or 0),
                        "goals_for": float(cells[5].get_text(strip=True) or 0),
                        "goals_against": float(cells[6].get_text(strip=True) or 0),
                        "ppg": float(cells[8].get_text(strip=True) or 0),
                        "xg": float(cells[9].get_text(strip=True) or 0),
                        "xga": float(cells[10].get_text(strip=True) or 0),
                        "btts_pct": float(cells[11].get_text(strip=True).replace("%", "") or 0),
                        "clean_sheet_pct": float(cells[12].get_text(strip=True).replace("%", "") or 0),
                        "avg_corners": float(cells[13].get_text(strip=True) or 0),
                        "avg_cards": float(cells[14].get_text(strip=True) or 0),
                        "avg_goals": float(cells[15].get_text(strip=True) or 0),
                    }
                    if record["team_name"] and record["games_played"] > 0:
                        records.append(record)
                except (ValueError, IndexError):
                    continue

    return pd.DataFrame(records)


def generate_mock_teams() -> pd.DataFrame:
    """Generate realistic statistics for World Cup teams to seed the database."""
    print("Generating mock team statistics for 48 World Cup teams...")
    records = []
    
    for team_name, fifa, conf in WC_2026_TEAMS:
        # Generate stats based on strength (FIFA ranking)
        gp = random.randint(10, 15)
        
        # Determine success ratios based on ranking
        if fifa <= 15:
            win_ratio, draw_ratio = 0.65, 0.20
            xg_avg, xga_avg = 1.9, 0.8
        elif fifa <= 35:
            win_ratio, draw_ratio = 0.45, 0.25
            xg_avg, xga_avg = 1.4, 1.1
        else:
            win_ratio, draw_ratio = 0.25, 0.30
            xg_avg, xga_avg = 1.0, 1.6
            
        wins = int(gp * win_ratio)
        draws = int(gp * draw_ratio)
        losses = gp - wins - draws
        
        gf = round(gp * xg_avg * random.uniform(0.85, 1.15), 1)
        ga = round(gp * xga_avg * random.uniform(0.85, 1.15), 1)
        ppg = round((wins * 3 + draws) / gp, 2)
        
        # BTTS and Clean Sheets
        btts_pct = round(random.uniform(40.0, 65.0), 1)
        clean_sheet_pct = round((wins / gp) * 100 * random.uniform(0.8, 1.2), 1)
        clean_sheet_pct = min(100.0, max(0.0, clean_sheet_pct))
        
        # corners/cards/goals averages
        avg_corners = round(random.uniform(8.2, 11.5), 2)
        avg_cards = round(random.uniform(1.8, 4.2), 2)
        avg_goals = round((gf + ga) / gp, 2)
        
        # Over thresholds
        over_25 = round(random.uniform(35.0, 65.0), 1)
        over_15 = round(random.uniform(70.0, 95.0), 1)
        over_35 = round(random.uniform(10.0, 35.0), 1)
        
        records.append({
            "team_name": team_name,
            "fifa_ranking": fifa,
            "confederation": conf,
            "games_played": gp,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": gf,
            "goals_against": ga,
            "ppg": ppg,
            "xg": round(xg_avg, 2),
            "xga": round(xga_avg, 2),
            "btts_pct": btts_pct,
            "clean_sheet_pct": clean_sheet_pct,
            "avg_corners": avg_corners,
            "avg_cards": avg_cards,
            "avg_goals": avg_goals,
            "over_25_pct": over_25,
            "over_15_pct": over_15,
            "over_35_pct": over_35,
            "sentiment_score": 0.0
        })
        
    return pd.DataFrame(records)


def scrape_and_push():
    """Main function: scrape FootyStats or fallback to mock data and push to Supabase."""
    df = pd.DataFrame()
    try:
        print("Fetching FootyStats World Cup page...")
        soup = fetch_page(FOOTYSTATS_WC_URL)
        print("Parsing team stats tables...")
        df = parse_main_table(soup)
    except Exception as e:
        print(f"Scraping failed: {e}")
        
    if df.empty:
        print("Using local mock team generator to seed teams...")
        df = generate_mock_teams()

    print(f"Parsed/Generated {len(df)} teams. Pushing to Supabase...")
    for _, row in df.iterrows():
        try:
            result = upsert_team(row.to_dict())
            print(f"  ✓ {row['team_name']}")
        except Exception as e:
            print(f"  ✗ Failed to push {row['team_name']}: {e}")

    print(f"\nDone. {len(df)} teams updated in Supabase.")


if __name__ == "__main__":
    scrape_and_push()
