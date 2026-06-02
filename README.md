# ⚽ Sporty-Opele
### *Finding edge where data meets the beautiful game.*

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)
![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E?logo=supabase&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active%20Development-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What Is This?

Sporty-Opele is a personal data science project that hunts for statistical edges in football — specifically the markets that bookmakers price lazily.

Not match results. Not who wins.

**Corners. Cards. Both Teams To Score. Asian Handicap. Goals Over/Under.**

The thesis: bookmakers spend 80% of their pricing effort on match outcome odds. Secondary markets are softer, less efficient, and more exploitable with the right model.

The first test case is the **FIFA World Cup 2026** (June 11 – July 19, 2026). 48 teams. 104 matches. A contained, high-signal environment to prove the system works before expanding to club football.

---

## How It Works

```
FootyStats (scraper)
        │
        ▼
Python Backend
  ├── Feature Engineering     ← team stats, form, sentiment
  ├── 5 ML Models             ← one per betting market
  └── Prediction Pipeline     ← runs daily before matchday
        │
        ▼
Supabase (PostgreSQL)
        │
        ▼
React Dashboard
  ├── Team Cards              ← all 48 WC teams + stats
  ├── Daily Predictions       ← today's matches + model output
  ├── Bet Slip                ← high-confidence picks only
  └── Accuracy Tracker        ← feedback loop, real-time model performance
```

There is no heavyweight orchestration layer. No Docker. No Airflow. Just Python scripts, a cloud database, and a clean React frontend. Simple enough to run on a laptop. Scalable enough to grow into something bigger.

---

## The Five Markets

| Market | Prediction | Model Target |
|---|---|---|
| **Corners** | Over / Under 9.5 | Total corners in 90 mins |
| **Cards** | Over / Under 3.5 | Total bookings (yellow=1, red=2) |
| **BTTS** | Yes / No | Both teams score at least once |
| **Asian Handicap** | Cover / No Cover | Home team covers -0.5 |
| **Goals** | Over / Under 2.5 | Total goals in 90 mins |

Each market has its own dedicated model. One model per market means cleaner features, easier debugging, and independent performance tracking.

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Data scraping | Python + BeautifulSoup | FootyStats has what we need — no paid API required |
| Sentiment | Reddit PRAW | Pre-match narrative as a model signal |
| Feature engineering | Pandas + NumPy | Flat feature matrix, one row per match |
| ML Models | scikit-learn (Random Forest + Calibration) | Calibrated probabilities, not just accuracy |
| Database | Supabase (PostgreSQL) | Free tier, real-time, React SDK |
| Frontend | React + Vite | Fast, component-based, direct Supabase integration |
| Feedback loop | Python script | Logs actual outcomes vs predictions post-match |

**No Docker. No Airflow. No dbt. No MLflow.** Those belong in a later phase when the model is proven.

---

## Project Structure

```
sporty-opele/
│
├── backend/
│   ├── scraper/
│   │   ├── footystats_scraper.py     # Pulls WC team stats from FootyStats
│   │   └── reddit_sentiment.py       # Reddit sentiment per team
│   │
│   ├── features/
│   │   └── feature_engineering.py    # Builds match feature matrix
│   │
│   ├── models/
│   │   ├── corners_model.py
│   │   ├── cards_model.py
│   │   ├── btts_model.py
│   │   ├── handicap_model.py
│   │   └── goals_model.py
│   │
│   ├── pipeline/
│   │   └── run_pipeline.py           # Master script: scrape → features → predict → push
│   │
│   ├── feedback/
│   │   └── log_outcomes.py           # Post-match: actual vs predicted
│   │
│   ├── db/
│   │   └── supabase_client.py        # DB connection + write helpers
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TeamCard.jsx
│   │   │   ├── MatchPredictions.jsx
│   │   │   ├── BetSlip.jsx
│   │   │   └── AccuracyTracker.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Teams.jsx
│   │   │   └── Performance.jsx
│   │   ├── lib/
│   │   │   └── supabaseClient.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── .env.example
│
├── db/
│   └── schema.sql                    # Full Supabase schema
│
├── README.md
└── .gitignore
```

---

## Database Schema (Supabase)

Six tables. Two views. Everything the pipeline writes and the dashboard reads.

| Table | Purpose |
|---|---|
| `wc_teams` | One row per World Cup team — scraped stats + sentiment score |
| `wc_fixtures` | Full WC 2026 match schedule + results (filled post-match) |
| `predictions` | Model output per market per fixture |
| `prediction_outcomes` | Actual result vs prediction — the feedback loop |
| `model_runs` | Training run metadata and evaluation metrics |

| View | Purpose |
|---|---|
| `todays_predictions` | Joins fixtures + predictions for today's matches |
| `market_accuracy` | Running accuracy % per market across all logged outcomes |

---

## Running the Pipeline

### Setup

```bash
# Backend
cd backend
cp .env.example .env        # Fill in Supabase + Reddit credentials
pip install -r requirements.txt

# Frontend
cd frontend
cp .env.example .env        # Fill in Supabase URL + anon key
npm install
npm run dev
```

### Daily matchday workflow

```bash
# 1. Scrape latest team stats + update sentiment + generate predictions
python backend/pipeline/run_pipeline.py

# 2. After the match, log outcomes (replace 12 with actual fixture ID)
python backend/feedback/log_outcomes.py --fixture_id 12
```

### Train models individually

```bash
python backend/models/corners_model.py
python backend/models/cards_model.py
python backend/models/btts_model.py
python backend/models/handicap_model.py
python backend/models/goals_model.py
```

---

## Modeling Philosophy

**Calibration over accuracy.** A model that says 65% and is right 65% of the time is more valuable than one that maximises raw prediction accuracy. Probability calibration is a primary metric.

**One model per market.** Corners and cards are driven by different factors. Separate models, separate feature sets, separate evaluation.

**Sentiment as a modifier, not a driver.** Reddit sentiment is a signal that shifts probabilities at the margin — not a standalone predictor. If the API rate-limits, it defaults to 0 and the pipeline continues.

**Walk-forward validation (when enough data exists).** Train on past, predict forward. No random train/test splits that mix time periods.

**The feedback loop is the product.** Predictions without outcome tracking are guesses. Every completed match is a data point that makes the next prediction better.

---

## Evaluation Metrics

| Metric | What It Measures |
|---|---|
| **Log-Loss** | Quality of predicted probabilities |
| **Brier Score** | Mean squared error between probabilities and outcomes |
| **Accuracy %** | Raw correct/incorrect per market (tracked in dashboard) |
| **Calibration** | Do predicted probabilities match observed frequencies? |

All metrics are tracked per market in the `prediction_outcomes` table and surfaced live in the Performance page of the dashboard.

---

## World Cup 2026 Scope

This project is intentionally scoped to the World Cup as a **proof of concept**. 48 teams. Fixed tournament. High data availability. Clear start and end date.

After the tournament, the plan is to:
- Expand to top club leagues (Premier League, La Liga, Serie A, Bundesliga)
- Add league-selection to the dashboard so users can switch contexts
- Retrain models on larger club football datasets
- Introduce automated scheduling via cron or a lightweight task runner

For now: World Cup. One tournament. Five markets. Let's see if the models have edge.

---

## Roadmap

- [x] Project restructure (World Cup 2026 focus)
- [x] Supabase schema design
- [x] FootyStats scraper
- [x] Reddit sentiment scraper
- [x] Feature engineering pipeline
- [x] 5 ML models (corners, cards, BTTS, handicap, goals)
- [x] Master pipeline script
- [x] Feedback loop (log_outcomes.py)
- [ ] React dashboard — Team Cards page
- [ ] React dashboard — Daily Predictions page
- [ ] React dashboard — Performance / Accuracy Tracker page
- [ ] Seed wc_fixtures with World Cup 2026 schedule
- [ ] Train models on Qatar 2022 historical data
- [ ] First live prediction run (June 11, 2026)
- [ ] Post-tournament model review
- [ ] Expand to club leagues

---

## Disclaimer

**For educational and research purposes only.**

Sporty-Opele is a statistical modelling experiment. It does not constitute financial advice, betting advice, or any guarantee of returns. Betting carries significant financial risk. All simulated results are based on historical data and do not predict future outcomes.

---

<p align="center">
Built with curiosity and too much football data ·
<a href="https://github.com/De-Akatsuki/sporty-opele">De-Akatsuki</a>
</p>
