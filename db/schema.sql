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

-- Processed features: one row per fixture for ML markets (see feature_eng.md)
CREATE TABLE IF NOT EXISTS processed_features (
    id                          SERIAL PRIMARY KEY,
    fixture_id                  INT NOT NULL UNIQUE REFERENCES wc_fixtures(id),
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    home_team                   TEXT,
    away_team                   TEXT,
    match_date                  DATE,
    home_corners_for_avg        FLOAT,
    home_corners_against_avg    FLOAT,
    away_corners_for_avg        FLOAT,
    away_corners_against_avg    FLOAT,
    total_corners_avg_combined  FLOAT,
    corner_dominance_home       FLOAT,
    is_cup_match                BOOLEAN,
    home_cards_per_game_avg     FLOAT,
    away_cards_per_game_avg     FLOAT,
    home_fouls_per_game_avg     FLOAT,
    away_fouls_per_game_avg     FLOAT,
    referee_cards_per_game_avg  FLOAT,
    referee_red_rate            FLOAT,
    is_derby                    BOOLEAN,
    match_stakes_index          FLOAT,
    home_scored_pct             FLOAT,
    home_conceded_pct           FLOAT,
    away_scored_pct             FLOAT,
    away_conceded_pct           FLOAT,
    home_clean_sheet_rate       FLOAT,
    away_clean_sheet_rate       FLOAT,
    h2h_btts_rate               FLOAT,
    btts_base_prob              FLOAT,
    home_elo_rating             FLOAT,
    away_elo_rating             FLOAT,
    elo_differential            FLOAT,
    home_win_rate_5             FLOAT,
    away_win_rate_5             FLOAT,
    implied_prob_home           FLOAT,
    implied_prob_away           FLOAT,
    implied_prob_draw           FLOAT,
    market_handicap_line        FLOAT,
    home_cover_rate_rolling     FLOAT,
    is_neutral_venue            BOOLEAN,
    home_goals_scored_avg       FLOAT,
    home_goals_conceded_avg     FLOAT,
    away_goals_scored_avg       FLOAT,
    away_goals_conceded_avg     FLOAT,
    total_goals_avg_combined    FLOAT,
    home_over25_rate            FLOAT,
    away_over25_rate            FLOAT,
    h2h_goals_avg               FLOAT,
    home_xg_avg                 FLOAT,
    away_xg_avg                 FLOAT,
    combined_xg                 FLOAT,
    implied_over_prob_25        FLOAT,
    match_importance_index      FLOAT,
    is_group_stage              BOOLEAN,
    sentiment_score             FLOAT DEFAULT 0.0,
    data_confidence             TEXT,
    label_corners_over          SMALLINT,
    label_bookings_over         SMALLINT,
    label_btts                  SMALLINT,
    label_handicap_cover        SMALLINT,
    label_goals_over25          SMALLINT
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
