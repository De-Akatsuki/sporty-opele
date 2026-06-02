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
