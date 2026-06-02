---
trigger: always_on
---

# 🤖 Sporty-Opele — Agent Rebuild Instructions
## World Cup 2026 Edition

> These are instructions for an AI agent to fully scaffold and build the Sporty-Opele project from scratch. Read everything before executing. Execute in order.

--

## 🎯 What This Project Is

**Sporty-Opele** is a football prediction system focused on the **FIFA World Cup 2026** (June 11 – July 19, 2026). It is NOT a match result predictor. It targets **alternative betting markets** — the ones where bookmaker pricing is softest:

- Total corners (over/under 9.5)
- Total cards (over/under 3.5)
- Both Teams To Score (BTTS — yes/no)
- Asian Handicap cover
- Goals over/under 2.5

The system has three layers:
1. **Backend (Python)** — scrapes data, engineers features, trains ML models, pushes predictions to Supabase
2. **Database (Supabase/PostgreSQL)** — stores all raw data, features, predictions, and feedback
3. **Frontend (React)** — dashboard that reads from Supabase and displays daily predictions, team cards, and model accuracy

--

## 🗂 Final Folder Structure to Create

```
sporty-opele/
│
├── backend/
│   ├── scraper/
│   │   ├── footystats_scraper.py       # Scrapes FootyStats for WC team stats
│   │   └── reddit_sentiment.py         # Scrapes Reddit for sentiment signals
│   │
│   ├── features/
│   │   └── feature_engineering.py      # Builds feature set per team per match
│   │
│   ├── models/
│   │   ├── corners_model.py            # Predicts total corners O/U 9.5
│   │   ├── cards_model.py              # Predicts total cards O/U 3.5
│   │   ├── btts_model.py               # Predicts BTTS yes/no
│   │   ├── handicap_model.py           # Predicts Asian handicap cover
│   │   └── goals_model.py              # Predicts goals O/U 2.5
│   │
│   ├── pipeline/
│   │   └── run_pipeline.py             # Master script: scrape → features → predict → push to Supabase
│   │
│   ├── feedback/
│   │   └── log_outcomes.py             # After match: logs actual result vs prediction
│   │
│   ├── db/
│   │   └── supabase_client.py          # Supabase connection and write helpers
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TeamCard.jsx             # Card component for each WC team
│   │   │   ├── MatchPredictions.jsx     # Daily match + predictions view
│   │   │   ├── BetSlip.jsx              # Today's high-confidence picks
│   │   │   └── AccuracyTracker.jsx      # Running model accuracy per market
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx            # Main daily view
│   │   │   ├── Teams.jsx                # All 48 WC teams cards
│   │   │   └── Performance.jsx          # Model performance over time
│   │   │
│   │   ├── lib/
│   │   │   └── supabaseClient.js        # Supabase JS client setup
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
│
├── db/
│   └── schema.sql                       # Full Supabase schema
│
├── README.md
└── .gitignore
```

---

## 🗄 Step 1 — Create the Supabase Schema

Create the file `db/schema.sql` with the following tables. Run this against your Supabase project SQL editor.

```sql
-- ============================================================
-- SPORTY-OPELE: World Cup 2026 Schema
-- ============================================================

-- Teams: one row per World Cup team
CREATE TABLE IF NOT EXISTS wc_teams (
    id SERIAL PRIMARY KEY,
    team_name TEXT NOT NULL UNIQUE,
    fifa_ranking INT,
    confederation TEXT,
    -- Scraped stats from FootyStats
    games_played INT,
    wins INT,
    draws INT,
    losses INT,
    goals_for FLOAT,
    goals_against FLOAT,
    ppg FLOAT,                     -- Points per game
    xg FLOAT,                      -- Expected goals for
    xga FLOAT,                     -- Expected goals against
    btts_pct FLOAT,                -- Both teams to score %
    clean_sheet_pct FLOAT,         -- Clean sheet %
    avg_corners FLOAT,             -- Average corners per game
    avg_cards FLOAT,               -- Average cards per game
    avg_goals FLOAT,               -- Average goals per game
    over_25_pct FLOAT,             -- % games with 2.5+ goals
    over_15_pct FLOAT,
    over_35_pct FLOAT,
    sentiment_score FLOAT,         -- Reddit sentiment (-1 to +1)
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Fixtures: World Cup 2026 match schedule
CREATE TABLE IF NOT EXISTS wc_fixtures (
    id SERIAL PRIMARY KEY,
    match_date DATE NOT NULL,
    kickoff_time TIME,
    home_team TEXT REFERENCES wc_teams(team_name),
    away_team TEXT REFERENCES wc_teams(team_name),
    stage TEXT,                    -- Group Stage, Round of 16, etc.
    group_name TEXT,               -- Group A, B, C...
    venue TEXT,
    city TEXT,
    result_home_goals INT,         -- Filled after match
    result_away_goals INT,
    result_home_corners INT,
    result_away_corners INT,
    result_total_cards INT,
    result_btts BOOLEAN,
    match_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Predictions: model output per market per match
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    fixture_id INT REFERENCES wc_fixtures(id),
    market TEXT NOT NULL,          -- 'corners', 'cards', 'btts', 'handicap', 'goals'
    prediction TEXT NOT NULL,      -- e.g. 'over', 'under', 'yes', 'no'
    probability FLOAT NOT NULL,    -- Model confidence 0-1
    confidence_tier TEXT,          -- 'High', 'Medium', 'Low'
    sentiment_signal FLOAT,        -- Sentiment score at prediction time
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Outcomes: actual result vs prediction (feedback loop)
CREATE TABLE IF NOT EXISTS prediction_outcomes (
    id SERIAL PRIMARY KEY,
    prediction_id INT REFERENCES predictions(id),
    fixture_id INT REFERENCES wc_fixtures(id),
    market TEXT NOT NULL,
    prediction TEXT NOT NULL,
    probability FLOAT,
    actual_outcome TEXT NOT NULL,  -- What actually happened
    correct BOOLEAN NOT NULL,      -- Did prediction match outcome?
    logged_at TIMESTAMPTZ DEFAULT NOW()
);

-- Model runs: track each training run
CREATE TABLE IF NOT EXISTS model_runs (
    id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,      -- e.g. 'corners_model_v1'
    market TEXT NOT NULL,
    accuracy FLOAT,
    log_loss FLOAT,
    brier_score FLOAT,
    training_samples INT,
    run_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- VIEWS for frontend
-- ============================================================

-- Today's predictions with fixture info
CREATE OR REPLACE VIEW todays_predictions AS
SELECT
    f.match_date,
    f.home_team,
    f.away_team,
    f.stage,
    f.group_name,
    f.kickoff_time,
    p.market,
    p.prediction,
    p.probability,
    p.confidence_tier,
    p.sentiment_signal
FROM predictions p
JOIN wc_fixtures f ON p.fixture_id = f.id
WHERE f.match_date = CURRENT_DATE
ORDER BY f.kickoff_time, p.market;

-- Model accuracy tracker per market
CREATE OR REPLACE VIEW market_accuracy AS
SELECT
    market,
    COUNT(*) AS total_predictions,
    SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS correct_predictions,
    ROUND(AVG(CASE WHEN correct THEN 1.0 ELSE 0.0 END) * 100, 2) AS accuracy_pct
FROM prediction_outcomes
GROUP BY market
ORDER BY accuracy_pct DESC;
```

---

## 🐍 Step 2 — Backend: Requirements

Create `backend/requirements.txt`:

```txt
requests==2.31.0
beautifulsoup4==4.12.2
pandas==2.1.0
numpy==1.24.0
scikit-learn==1.3.0
supabase==2.3.0
python-dotenv==1.0.0
praw==7.7.1
schedule==1.2.0
lxml==4.9.3
```

---

## 🐍 Step 3 — Backend: Environment Variables

Create `backend/.env.example`:

```env
# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Reddit (PRAW) — create app at reddit.com/prefs/apps
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=sporty-opele-sentiment/1.0
```

---

## 🐍 Step 4 — Backend: Supabase Client

Create `backend/db/supabase_client.py`:

```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_team(team_data: dict):
    """Insert or update a team record."""
    return supabase.table("wc_teams").upsert(team_data, on_conflict="team_name").execute()


def insert_prediction(prediction_data: dict):
    """Insert a new prediction."""
    return supabase.table("predictions").insert(prediction_data).execute()


def get_fixtures_for_date(date: str):
    """Get all fixtures for a given date (YYYY-MM-DD)."""
    return supabase.table("wc_fixtures").select("*").eq("match_date", date).execute()


def log_outcome(outcome_data: dict):
    """Log actual match outcome vs prediction."""
    return supabase.table("prediction_outcomes").insert(outcome_data).execute()
```

---

## 🐍 Step 5 — Backend: FootyStats Scraper

Create `backend/scraper/footystats_scraper.py`:

```python
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


def fetch_page(url: str) -> BeautifulSoup:
    """Fetch a page and return a BeautifulSoup object."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    time.sleep(2)  # Polite crawl delay
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

    return pd