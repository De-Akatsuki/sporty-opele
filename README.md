# ⚽ Sporty-Opele: Football Prediction System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-2.x-017CEE?logo=apacheairflow&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Railway](https://img.shields.io/badge/Deploy-Railway-0B0D0E?logo=railway&logoColor=white)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

> *Finding the edge where data meets the beautiful game.*

**Sporty-Opele** is a personal data science project built to uncover statistical advantages in football through rigorous data analytics, feature engineering, and machine learning. The goal is not to predict football — it's to build a disciplined, reproducible system that models probability better than the market does, over time.

---

## 📌 Table of Contents

- [Project Goals](#-project-goals)
- [Architecture Overview](#-architecture-overview)
- [Tech Stack](#-tech-stack)
- [Open Source Tools](#-open-source-tools)
- [Project Structure](#-project-structure)
- [Installation & Setup](#️-installation--setup)
- [Infrastructure Setup](#-infrastructure-setup)
- [Workflow & Pipeline](#-workflow--pipeline)
- [Usage](#-usage)
- [Modeling Philosophy](#-modeling-philosophy)
- [Evaluation & Backtesting](#-evaluation--backtesting)
- [Roadmap](#-roadmap)
- [Where to Start](#-where-to-start)
- [Contributing](#-contributing)
- [Disclaimer](#️-disclaimer)

---

## 🎯 Project Goals

This project is built around three core objectives:

1. **Statistical Edge** — Identify situations where modelled probabilities diverge meaningfully from bookmaker-implied probabilities, pointing to potential value bets.
2. **Reproducibility** — Every step of the pipeline from data ingestion to model evaluation should be scriptable, versioned, and reproducible.
3. **Research Integrity** — All results should be validated on held-out data with proper walk-forward backtesting. No cherry-picking, no look-ahead bias.

This is a long-term research project, not a betting bot. Results are measured in model skill (calibration, log-loss, Brier score) and simulated EV — not short-term profit.

---

## 🏗 Architecture Overview

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL DATA SOURCES                          │
│   football-data.co.uk │ API-Football │ FBref / Understat (xG data)      │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ HTTP / REST API calls
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER  (Docker)                       │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Apache Airflow                               │   │
│   │                                                                 │   │
│   │   DAG: ingest_fixtures   →  DAG: build_features                │   │
│   │          ↓                          ↓                          │   │
│   │   DAG: train_models      →  DAG: run_evaluation                │   │
│   │          ↓                          ↓                          │   │
│   │   DAG: generate_predictions  →  DAG: write_to_db               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   Scheduled on matchday cadence (e.g. weekly, pre-gameweek)             │
└───────────────────┬─────────────────────────┬───────────────────────────┘
                    │                         │
          writes raw data             writes predictions
                    │                  & model results
                    ▼                         ▼
┌───────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                    │
│                                                                        │
│   ┌─────────────────────────┐    ┌──────────────────────────────────┐  │
│   │    Local PostgreSQL      │    │         Supabase (Cloud)         │  │
│   │  (Development / Testing) │    │      (Production Database)       │  │
│   │                          │    │                                  │  │
│   │  • raw_matches           │◄──►│  • raw_matches                   │  │
│   │  • processed_features    │    │  • processed_features            │  │
│   │  • predictions           │    │  • predictions                   │  │
│   │  • model_runs            │    │  • model_runs                    │  │
│   │  • backtest_results      │    │  • backtest_results              │  │
│   │                          │    │  • odds_history                  │  │
│   └──────────────────────────┘    └──────────────────────────────────┘  │
│                                          ▲         ▲                    │
│                                          │         │                    │
│                              REST API    │         │  Realtime / Auth   │
└──────────────────────────────────────────┼─────────┼────────────────────┘
                                           │         │
                    ┌──────────────────────┘         └──────────────────┐
                    ▼                                                   ▼
┌───────────────────────────────────┐         ┌────────────────────────────┐
│     ML PIPELINE  (src/ scripts)    │         │    DEPLOYMENT  (Railway)    │
│                                   │         │                            │
│  ingestion → features → train     │         │  • Scheduled pipeline runs │
│       ↓            ↓       ↓      │         │  • Prediction API          │
│  data/raw/  processed/  models/   │         │    (FastAPI - planned)      │
│                                   │         │  • Env var management      │
│  Artefacts: .pkl / .joblib        │         │  • Persistent service host │
└───────────────────────────────────┘         └────────────────────────────┘
                    │
                    │ model metrics + predictions → Supabase
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  ANALYTICS & VISUALISATION LAYER  (Docker)              │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                        Metabase                                  │  │
│   │                                                                  │  │
│   │  Dashboards connected directly to Supabase (PostgreSQL)          │  │
│   │                                                                  │  │
│   │  • Model performance over time (log-loss, Brier, ROI)            │  │
│   │  • Prediction vs. actual results                                 │  │
│   │  • CLV tracker (model odds vs. closing line)                     │  │
│   │  • EV opportunity heatmaps by league / market                    │  │
│   │  • Feature importance trends                                     │  │
│   └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Environment Strategy

| Environment | Database | Orchestration | Purpose |
|---|---|---|---|
| **Local Dev** | Local PostgreSQL | Manual script runs | Active development & debugging |
| **Staging / Test** | Local PostgreSQL | Airflow (Docker) | Test DAGs and pipeline logic |
| **Production** | Supabase | Airflow (Docker) | Live pipeline, scheduled runs |
| **Serving** | Supabase | Railway | Persistent prediction API & services |

### Data Flow Summary

```
APIs  ──►  Airflow DAG  ──►  src/ingestion/  ──►  DB: raw_matches
                │
                ▼
           src/features/  ──►  DB: processed_features
                │
                ▼
           src/models/   ──►  models/*.joblib  +  DB: model_runs
                │
                ▼
           src/evaluation/  ──►  DB: backtest_results  ──►  Metabase
```

---

## 🛠 Tech Stack

### Infrastructure

| Component | Tool | Role |
|---|---|---|
| **Orchestration** | Apache Airflow (Docker) | Schedule and run pipeline DAGs |
| **Production DB** | Supabase (PostgreSQL) | Cloud storage for all datasets and results |
| **Dev DB** | Local PostgreSQL | Local dev mirror, testing, schema iteration |
| **Containerisation** | Docker + Docker Compose | Run Airflow, Metabase, and local Postgres in isolation |
| **Deployment** | Railway | Host persistent services, scheduled jobs, and future API |
| **BI / Dashboards** | Metabase (Docker) | Visual analytics connected to Supabase |

### Data Science

| Layer | Tools |
|---|---|
| Language | Python 3.10+ |
| Data Handling | `pandas`, `numpy` |
| Database Client | `psycopg2`, `SQLAlchemy`, `supabase-py` |
| Machine Learning | `scikit-learn`, `xgboost`, `lightgbm` |
| Model Serialization | `joblib` |
| Experiment Tracking | `MLflow` *(planned)* |
| Notebooks / EDA | `Jupyter`, `matplotlib`, `seaborn`, `plotly` |
| Configuration | `python-dotenv`, `pydantic-settings` |
| Testing | `pytest` |

### External Data Sources

| Source | Data Provided | Access |
|---|---|---|
| [football-data.co.uk](https://football-data.co.uk) | Historical match results + odds (CSV) | Free |
| [API-Football](https://api-football.com) | Live fixtures, stats, standings | Freemium API |
| [FBref](https://fbref.com) | Advanced stats, xG, progressive metrics | Free (scraping) |
| [Understat](https://understat.com) | xG data per match and shot | Free (scraping) |

---

## 🔧 Open Source Tools

These are the open source tools integrated into or planned for this project, beyond the core Python ecosystem.

### Apache Airflow
**Role: Pipeline Orchestration**
Airflow runs as a Dockerised service and manages the scheduling and execution of all pipeline stages as DAGs (Directed Acyclic Graphs). Each stage of the pipeline (ingest → features → train → evaluate → predict) maps to a dedicated DAG, enabling dependency management, retry logic, and run history visibility via the Airflow UI.

### Metabase
**Role: Analytics & Dashboarding**
Metabase runs as a Dockerised service connected directly to Supabase via a PostgreSQL connection. It provides a no-code interface to build dashboards tracking model performance, prediction accuracy, CLV, and EV trends over time — without needing to write frontend code.

### PostgreSQL
**Role: Relational Data Store (both Local and via Supabase)**
All structured data — raw match records, engineered features, predictions, model metadata, and backtest results — is stored in PostgreSQL. The same schema runs locally for development and in Supabase for production.

### MLflow *(planned)*
**Role: Experiment Tracking**
MLflow will track all training runs with logged parameters, metrics, and model artefacts. Enables side-by-side comparison of model versions and a centralised model registry.

### Great Expectations *(planned)*
**Role: Data Quality Validation**
Great Expectations will be used to define and enforce expectations on ingested data (e.g. no null match results, valid date ranges, expected column schemas). Pipeline runs will fail fast if data quality checks are not met.

### dbt (Data Build Tool) *(planned)*
**Role: SQL-based Transformations**
dbt will manage the SQL transformation layer that sits between raw ingested data and processed feature tables in the database, giving full lineage, testing, and documentation of all data transformations.

### Docker Compose
**Role: Local Service Orchestration**
A `docker-compose.yml` at the project root brings up Airflow (webserver + scheduler + worker), Metabase, and a local PostgreSQL instance together as a unified local environment with a single command.

---

## 📂 Project Structure

```text
sporty-opele/
├── config/                        # Global configuration
│   └── settings.py                # Centralised config: paths, DB URLs, API keys, hyperparams
│
├── dags/                          # Airflow DAG definitions
│   ├── dag_ingest.py              # Scheduled data ingestion DAG
│   ├── dag_features.py            # Feature engineering DAG
│   ├── dag_train.py               # Model training DAG
│   ├── dag_evaluate.py            # Backtesting and evaluation DAG
│   └── dag_predict.py             # Gameweek prediction generation DAG
│
├── data/                          # Data assets — never committed to Git
│   ├── raw/                       # Immutable source data (API pulls, CSV downloads)
│   ├── processed/                 # ML-ready feature datasets
│   └── external/                  # Reference data (Elo tables, fixture calendars)
│
├── db/                            # Database layer
│   ├── schema.sql                 # Table definitions (run once to initialise DB)
│   ├── migrations/                # Incremental schema changes
│   └── queries/                   # Reusable SQL queries
│
├── docker/                        # Docker configuration
│   ├── airflow/                   # Airflow-specific Dockerfile and config
│   └── metabase/                  # Metabase config (if custom setup needed)
│
├── models/                        # Trained model artefacts
│   └── *.joblib                   # Serialised models (versioned: model_YYYY-MM-DD.joblib)
│
├── notebooks/                     # Jupyter notebooks for EDA and prototyping
│   ├── 01_eda_raw_data.ipynb
│   ├── 02_feature_exploration.ipynb
│   ├── 03_model_prototyping.ipynb
│   └── 04_odds_calibration.ipynb
│
├── outputs/                       # Generated outputs
│   ├── plots/                     # Visualisations from EDA and evaluation
│   ├── reports/                   # Backtest reports and metric summaries
│   └── predictions/               # Gameweek prediction CSVs
│
├── src/                           # Core source code
│   ├── ingestion/                 # Data fetching and storage
│   │   ├── fetch_fixtures.py      # Pull upcoming fixture lists
│   │   ├── fetch_results.py       # Pull historical match results
│   │   ├── fetch_odds.py          # Pull historical and live odds
│   │   └── db_writer.py           # Write raw data to PostgreSQL / Supabase
│   │
│   ├── features/                  # Feature engineering
│   │   ├── rolling_stats.py       # Rolling form windows (last 3, 5, 10 matches)
│   │   ├── elo.py                 # Elo rating system per team
│   │   ├── h2h.py                 # Head-to-head historical features
│   │   ├── xg_features.py         # xG-based features (shots, expected goals)
│   │   └── pipeline.py            # Master feature pipeline runner
│   │
│   ├── models/                    # ML training, tuning, inference
│   │   ├── train.py               # Train model on feature set
│   │   ├── predict.py             # Generate predictions for upcoming fixtures
│   │   └── tune.py                # Hyperparameter search (GridSearch / Optuna)
│   │
│   └── evaluation/                # Validation and backtesting
│       ├── backtest.py            # Walk-forward backtesting engine
│       ├── metrics.py             # Log-loss, Brier score, calibration
│       └── ev_analysis.py         # Expected value vs. market odds
│
├── tests/                         # Automated tests
│   ├── test_ingestion.py
│   ├── test_features.py
│   ├── test_models.py
│   └── test_db.py
│
├── docker-compose.yml             # Brings up Airflow + Metabase + Local Postgres
├── .env                           # Local secrets — never committed
├── .env.example                   # Template of required environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10 or higher
- Docker + Docker Compose
- A Supabase account and project
- A Railway account (for deployment)

### Local Setup

**1. Clone the repository**
```bash
git clone https://github.com/De-Akatsuki/sporty-opele.git
cd sporty-opele
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**
```bash
cp .env.example .env
```

Fill in your `.env`:
```env
# --- Data Sources ---
API_FOOTBALL_KEY=your_api_key_here

# --- Local PostgreSQL ---
LOCAL_DB_URL=postgresql://user:password@localhost:5432/sporty_opele

# --- Supabase (Production) ---
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_key
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# --- Environment ---
ENV=development   # or production
DATA_DIR=./data
MODEL_DIR=./models
```

> ⚠️ Never commit `.env` to version control. It is listed in `.gitignore` by default.

---

## 🐳 Infrastructure Setup

### Spin up local services with Docker Compose

The `docker-compose.yml` at the project root brings up three services together:

```bash
docker compose up -d
```

| Service | Local URL | Purpose |
|---|---|---|
| Airflow Webserver | http://localhost:8080 | DAG management UI (admin/admin) |
| Metabase | http://localhost:3000 | Analytics dashboard UI |
| Local PostgreSQL | localhost:5432 | Development database |

**First-time Airflow initialisation:**
```bash
docker compose run airflow-init
```

### Initialise the database schema

Run the schema script against your target database:

```bash
# Local dev
psql $LOCAL_DB_URL -f db/schema.sql

# Supabase (production) — run via Supabase SQL Editor or psql
psql $SUPABASE_DB_URL -f db/schema.sql
```

### Connect Metabase to Supabase

1. Open Metabase at http://localhost:3000
2. Go to **Admin → Databases → Add database**
3. Select **PostgreSQL** and enter your Supabase connection details
4. Metabase will introspect the schema and make all tables available for querying

### Deploy services to Railway

Railway hosts any persistent services (e.g. a scheduled prediction API or a lightweight pipeline runner):

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link

# Set environment variables in Railway dashboard or via CLI
railway variables set SUPABASE_URL=...

# Deploy
railway up
```

---

## 🔄 Workflow & Pipeline

### End-to-End Data Flow

```
┌──────────────────┐
│  External APIs   │  football-data.co.uk, API-Football, FBref
└────────┬─────────┘
         │  Triggered by Airflow DAG (dag_ingest.py)
         ▼
┌──────────────────┐
│  src/ingestion/  │  Fetch → Parse → Validate → Write to DB
│  → raw_matches   │
└────────┬─────────┘
         │  Triggered by Airflow DAG (dag_features.py)
         ▼
┌──────────────────┐
│  src/features/   │  Roll averages, Elo, H2H, xG features
│  → processed_    │
│    features      │
└────────┬─────────┘
         │  Triggered by Airflow DAG (dag_train.py)
         ▼
┌──────────────────┐
│  src/models/     │  Train on feature set → Save .joblib → Log to DB
│  → models/       │
│  → model_runs    │
└────────┬─────────┘
         │  Triggered by Airflow DAG (dag_evaluate.py)
         ▼
┌──────────────────┐
│ src/evaluation/  │  Walk-forward backtest → Metrics → Write to DB
│ → backtest_      │
│   results        │
└────────┬─────────┘
         │  Triggered by Airflow DAG (dag_predict.py)
         ▼
┌──────────────────┐
│  src/models/     │  Generate gameweek predictions → Write to DB
│  predict.py      │
│  → predictions   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    Metabase      │  Dashboards pulling from Supabase in real time
└──────────────────┘
```

### Stage Descriptions

**Ingestion (`src/ingestion/`)** — Connects to external data sources, fetches raw match results, fixtures, and odds. Data is written to the `raw_matches` and `odds_history` tables in PostgreSQL. Raw source files are also archived in `data/raw/` and are never modified.

**Feature Engineering (`src/features/`)** — Processes raw match records into ML-ready features. Computes rolling form windows, Elo ratings, head-to-head history, and xG-derived metrics. All features are lagged to prevent look-ahead bias. Output is written to the `processed_features` table.

**Training (`src/models/train.py`)** — Reads from `processed_features`, trains the configured algorithm, and serialises the model artefact to `models/`. Each training run is logged to the `model_runs` table with parameters, metrics, and a run ID.

**Evaluation (`src/evaluation/`)** — Runs walk-forward backtesting across historical seasons. Computes calibration quality and simulated EV. Results are written to `backtest_results` for tracking over time.

**Prediction (`src/models/predict.py`)** — Loads the latest trained model, generates probability predictions for upcoming fixtures, and writes them to the `predictions` table in Supabase, where Metabase can surface them.

---

## 🖥 Usage

### Start all local services
```bash
docker compose up -d
```

### Run individual pipeline stages manually
```bash
python src/ingestion/fetch_results.py
python src/features/pipeline.py
python src/models/train.py --model xgboost --season 2023-24
python src/evaluation/backtest.py
python src/models/predict.py --gameweek 22
```

### Trigger an Airflow DAG manually
```bash
# Via CLI inside the Airflow container
docker exec -it airflow-scheduler airflow dags trigger dag_ingest
```

### Run tests
```bash
pytest tests/
```

### Launch EDA notebooks
```bash
jupyter notebook notebooks/
```

---

## 🧠 Modeling Philosophy

- **No look-ahead bias.** Features are computed only from data available before the match being predicted. Rolling windows and Elo ratings are always lagged by at least one matchday.
- **Calibration over accuracy.** A model that says "60% home win" and is right 60% of the time is more valuable than one that maximises raw accuracy. Probability calibration is a primary evaluation criterion.
- **Market awareness.** The bookmaker's implied probability is treated as a baseline to beat, not a label to predict. Finding divergence between model output and market odds is the actual objective.
- **Walk-forward backtesting.** Models are evaluated by training on past seasons and predicting forward in sequence — no random train/test splits that mix temporal data.
- **Discipline over optimism.** If a model does not beat the closing line consistently, it does not go to production. Simulated profits mean nothing; CLV does.

---

## 📊 Evaluation & Backtesting

| Metric | Purpose |
|---|---|
| **Log-Loss** | Quality of predicted probabilities |
| **Brier Score** | Mean squared error between probabilities and outcomes |
| **Calibration Curve** | Visual check that predicted probabilities match observed frequencies |
| **ROI (simulated)** | Return on investment if flat-staking on positive EV opportunities |
| **CLV (Closing Line Value)** | How model odds compare to closing market odds — the gold standard of edge measurement |

> All backtests use walk-forward validation. Results are stored in the `backtest_results` table in Supabase and visualised in Metabase.

---

## 🗺 Roadmap

### Phase 1 — Foundation *(current)*
- [x] Set up modular project structure and GitHub repo
- [ ] Configure `docker-compose.yml` for Airflow + Metabase + Local Postgres
- [ ] Initialise `db/schema.sql` with core table definitions
- [ ] Write ingestion scripts (football-data.co.uk CSV baseline)
- [ ] Set up initial EDA notebooks
- [ ] Build baseline model (Logistic Regression)
- [ ] Implement walk-forward backtesting scaffold

### Phase 2 — Feature Development
- [ ] Rolling form windows (last 3, 5, 10 matches)
- [ ] Elo rating system per team
- [ ] Head-to-head historical feature builder
- [ ] Goal expectation (xG) integration via Understat
- [ ] Home/away performance splits and venue effects

### Phase 3 — Advanced Modeling
- [ ] Gradient Boosting (XGBoost / LightGBM)
- [ ] Hyperparameter tuning with Optuna
- [ ] Ensemble / stacking approach
- [ ] Probability calibration (Platt scaling / isotonic regression)
- [ ] MLflow experiment tracking integration

### Phase 4 — Production & Automation
- [ ] Full Airflow DAG suite for end-to-end automation
- [ ] Automated matchday prediction generation
- [ ] CLV monitoring dashboard in Metabase
- [ ] Great Expectations for data quality checks
- [ ] dbt transformation layer over raw tables
- [ ] Prediction API on Railway (FastAPI)

---

## 🚦 Where to Start

The project structure is in place and the repo is set up. Here is the exact sequence to go from zero to first working pipeline:

**Step 1 — Docker Compose setup**
Write `docker-compose.yml` to bring up Airflow, Metabase, and Local PostgreSQL together. Verify all three services are accessible before writing any pipeline code.

**Step 2 — Database schema**
Write `db/schema.sql` with your core tables: `raw_matches`, `processed_features`, `predictions`, `model_runs`, `backtest_results`, `odds_history`. Run it against your local Postgres first, then against Supabase.

**Step 3 — First ingestion script**
Start with `football-data.co.uk` — it serves historical data as flat CSVs, no API key needed. Write `src/ingestion/fetch_results.py` to download the CSV, parse it with pandas, and write it to the `raw_matches` table. Confirm rows land in both local Postgres and Supabase.

**Step 4 — First EDA notebook**
With data in the database, open `notebooks/01_eda_raw_data.ipynb`. Query from PostgreSQL, explore distributions, check for nulls, understand the shape of what you have. This will directly inform which features are feasible to build.

**Step 5 — First feature set**
Build `src/features/rolling_stats.py` — rolling home/away form windows are the single highest-signal starting feature. Keep it simple. Save output to `processed_features`.

**Step 6 — Baseline model**
Train Logistic Regression on your first feature set. The goal is not accuracy — it's to have a calibrated probability output to compare against bookmaker odds. Log the run to `model_runs`.

**Step 7 — Backtest**
Run `src/evaluation/backtest.py` across at least 2 seasons of held-out data. Log results to `backtest_results`. Check calibration curve before anything else.

**Step 8 — Metabase dashboard**
With data in Supabase, connect Metabase and build a simple dashboard: predictions vs actuals, model log-loss over time, Brier score per season. This becomes your ongoing performance monitor.

**Step 9 — First Airflow DAG**
Wire `dag_ingest.py` to run `fetch_results.py` on a schedule. Confirm it runs, writes data, and fails gracefully if the source is unavailable.

From this point, you iterate: more features, better models, more DAGs.

---

## 🤝 Contributing

This is primarily a personal research project, but structured contributions are welcome.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Follow the existing module structure — new code belongs in the appropriate `src/` subdirectory
4. Write or update tests in `tests/` for any new logic
5. Commit clearly: `git commit -m "feat: add Elo rating feature builder"`
6. Open a pull request with a description of what was added and why

Please keep contributions focused on the data science pipeline. This is not a web app — UI additions are out of scope.

---

## ⚠️ Disclaimer

**For educational and research purposes only.**

Sporty-Opele is a statistical modelling experiment. It does not constitute financial advice, betting advice, or any guarantee of returns. Betting carries significant financial risk. All simulated results are based on historical data and do not predict future outcomes. I accept no responsibility for financial decisions made using outputs from this project.

---

<p align="center">
Built with curiosity and too much football data ·
<a href="https://github.com/De-Akatsuki/sporty-opele">De-Akatsuki</a>
</p>