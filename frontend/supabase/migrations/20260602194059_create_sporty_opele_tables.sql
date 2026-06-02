/*
  Sporty-Opele — aligned with db/schema.sql and backend pipeline.
  Apply via Supabase SQL editor or CLI migrations.
*/

-- wc_teams
CREATE TABLE IF NOT EXISTS wc_teams (
    id SERIAL PRIMARY KEY,
    team_name TEXT NOT NULL UNIQUE,
    fifa_ranking INT,
    confederation TEXT,
    games_played INT,
    wins INT,
    draws INT,
    losses INT,
    goals_for FLOAT,
    goals_against FLOAT,
    ppg FLOAT,
    xg FLOAT,
    xga FLOAT,
    btts_pct FLOAT,
    clean_sheet_pct FLOAT,
    avg_corners FLOAT,
    avg_cards FLOAT,
    avg_goals FLOAT,
    over_25_pct FLOAT,
    over_15_pct FLOAT,
    over_35_pct FLOAT,
    sentiment_score FLOAT DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- wc_fixtures
CREATE TABLE IF NOT EXISTS wc_fixtures (
    id SERIAL PRIMARY KEY,
    match_date DATE NOT NULL,
    kickoff_time TIME,
    home_team TEXT REFERENCES wc_teams(team_name),
    away_team TEXT REFERENCES wc_teams(team_name),
    stage TEXT,
    group_name TEXT,
    venue TEXT,
    city TEXT,
    result_home_goals INT,
    result_away_goals INT,
    result_home_corners INT,
    result_away_corners INT,
    result_total_cards INT,
    result_btts BOOLEAN,
    match_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- predictions
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    fixture_id INT REFERENCES wc_fixtures(id) ON DELETE CASCADE,
    market TEXT NOT NULL,
    prediction TEXT NOT NULL,
    probability FLOAT NOT NULL,
    confidence_tier TEXT,
    sentiment_signal FLOAT,
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- processed_features (feature engineering pipeline output)
CREATE TABLE IF NOT EXISTS processed_features (
    id SERIAL PRIMARY KEY,
    fixture_id INT NOT NULL UNIQUE REFERENCES wc_fixtures(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    home_team TEXT,
    away_team TEXT,
    match_date DATE,
    home_corners_for_avg FLOAT,
    home_corners_against_avg FLOAT,
    away_corners_for_avg FLOAT,
    away_corners_against_avg FLOAT,
    total_corners_avg_combined FLOAT,
    corner_dominance_home FLOAT,
    is_cup_match BOOLEAN,
    home_cards_per_game_avg FLOAT,
    away_cards_per_game_avg FLOAT,
    home_fouls_per_game_avg FLOAT,
    away_fouls_per_game_avg FLOAT,
    referee_cards_per_game_avg FLOAT,
    referee_red_rate FLOAT,
    is_derby BOOLEAN,
    match_stakes_index FLOAT,
    home_scored_pct FLOAT,
    home_conceded_pct FLOAT,
    away_scored_pct FLOAT,
    away_conceded_pct FLOAT,
    home_clean_sheet_rate FLOAT,
    away_clean_sheet_rate FLOAT,
    h2h_btts_rate FLOAT,
    btts_base_prob FLOAT,
    home_elo_rating FLOAT,
    away_elo_rating FLOAT,
    elo_differential FLOAT,
    home_win_rate_5 FLOAT,
    away_win_rate_5 FLOAT,
    implied_prob_home FLOAT,
    implied_prob_away FLOAT,
    implied_prob_draw FLOAT,
    market_handicap_line FLOAT,
    home_cover_rate_rolling FLOAT,
    is_neutral_venue BOOLEAN,
    home_goals_scored_avg FLOAT,
    home_goals_conceded_avg FLOAT,
    away_goals_scored_avg FLOAT,
    away_goals_conceded_avg FLOAT,
    total_goals_avg_combined FLOAT,
    home_over25_rate FLOAT,
    away_over25_rate FLOAT,
    h2h_goals_avg FLOAT,
    home_xg_avg FLOAT,
    away_xg_avg FLOAT,
    combined_xg FLOAT,
    implied_over_prob_25 FLOAT,
    match_importance_index FLOAT,
    is_group_stage BOOLEAN,
    sentiment_score FLOAT DEFAULT 0.0,
    data_confidence TEXT,
    label_corners_over SMALLINT,
    label_bookings_over SMALLINT,
    label_btts SMALLINT,
    label_handicap_cover SMALLINT,
    label_goals_over25 SMALLINT
);

-- prediction_outcomes (feedback loop)
CREATE TABLE IF NOT EXISTS prediction_outcomes (
    id SERIAL PRIMARY KEY,
    prediction_id INT REFERENCES predictions(id),
    fixture_id INT REFERENCES wc_fixtures(id),
    market TEXT NOT NULL,
    prediction TEXT NOT NULL,
    probability FLOAT,
    actual_outcome TEXT NOT NULL,
    correct BOOLEAN NOT NULL,
    logged_at TIMESTAMPTZ DEFAULT NOW()
);

-- model_runs
CREATE TABLE IF NOT EXISTS model_runs (
    id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    market TEXT NOT NULL,
    accuracy FLOAT,
    log_loss FLOAT,
    brier_score FLOAT,
    training_samples INT,
    run_at TIMESTAMPTZ DEFAULT NOW()
);

-- Views
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

CREATE OR REPLACE VIEW market_accuracy AS
SELECT
    market,
    COUNT(*) AS total_predictions,
    SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS correct_predictions,
    ROUND(AVG(CASE WHEN correct THEN 1.0 ELSE 0.0 END) * 100, 2) AS accuracy_pct
FROM prediction_outcomes
GROUP BY market
ORDER BY accuracy_pct DESC;

-- RLS (read-only analytics app)
ALTER TABLE wc_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE wc_fixtures ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read wc_teams" ON wc_teams FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read wc_fixtures" ON wc_fixtures FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read predictions" ON predictions FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read processed_features" ON processed_features FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read prediction_outcomes" ON prediction_outcomes FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read model_runs" ON model_runs FOR SELECT TO anon, authenticated USING (true);

CREATE INDEX IF NOT EXISTS idx_wc_fixtures_match_date ON wc_fixtures(match_date);
CREATE INDEX IF NOT EXISTS idx_wc_fixtures_completed ON wc_fixtures(match_completed);
CREATE INDEX IF NOT EXISTS idx_predictions_fixture_id ON predictions(fixture_id);
CREATE INDEX IF NOT EXISTS idx_processed_features_fixture_id ON processed_features(fixture_id);
