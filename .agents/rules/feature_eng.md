# 📊 Sporty-Opele — Feature Engineering Market Reference
## For Agent Use: Targeted Betting Markets & Feature Signals

> **Purpose:** This document defines the betting markets Sporty-Opele targets and maps each one to the features the engineering pipeline must produce. The agent should use this as the authoritative reference when building or updating `src/features/feature_engineering.py`, `src/models/`, and the Supabase `processed_features` table schema.
>
> **Scope:** Five active prediction markets, drawn from eight SportyBet market categories. Only build features for what is listed here — do not scope-creep into other market types.

---

## ⚽ The 5 Prediction Targets

| # | Market Name | Prediction Target | Model Output |
|---|---|---|---|
| 1 | **Total Corners Over/Under** | Will total corners exceed 9.5? | Binary (Over / Under) + probability |
| 2 | **Total Bookings Over/Under** | Will total bookings exceed 3.5? | Binary (Over / Under) + probability |
| 3 | **Both Teams To Score (BTTS)** | Will both teams score? | Binary (Yes / No) + probability |
| 4 | **Asian Handicap** | Will the favoured team cover the handicap? | Binary (Cover / No Cover) + probability |
| 5 | **Goals Over/Under 2.5** | Will total goals exceed 2.5? | Binary (Over / Under) + probability |

---

## 📚 Market Category Reference

The following sections document the SportyBet market rules relevant to each prediction target. The agent must understand these rules to correctly label training data and validate outcomes.

---

## Category 1 — Corner Markets (Target: Total Corners O/U 9.5)

### Settlement Rules
- Only **taken** corners count. Corners awarded but not taken are excluded.
- Corner time = time the kick **is taken**, not when it is awarded.
- Regular time + injury time only. Overtime not included.

### Relevant Markets for Labelling

| Market | Description | Used For |
|---|---|---|
| **Corners Over/Under** | Total corners in regular time vs. a given line | **Primary label**: over/under 9.5 |
| **Corner Range** | Range bucket the total corners fall into | Validation cross-check |
| **Corners 1X2** | Which team earns the most corners | Secondary signal (attacking intent) |
| **Home Team Corners O/U** | Home team's corner total vs. line | Feature: home team corner rate |
| **Away Team Corners O/U** | Away team's corner total vs. line | Feature: away team corner rate |
| **1st Half Corners O/U** | Total corners in 1st half | Feature: first-half corner pace |
| **Odd/Even Corners** | Parity of total corners | Validation only |

### Features to Engineer

```python
# Rolling averages (last 5, 10 matches)
home_corners_for_avg       # avg corners earned per game (home team)
home_corners_against_avg   # avg corners conceded per game (home team)
away_corners_for_avg
away_corners_against_avg

# Match-level derived
total_corners_avg_combined  # (home_for + away_for + home_against + away_against) / 2
corner_dominance_home       # home_for / (home_for + away_for)  — attacking pressure proxy

# Context
is_cup_match               # cup matches tend to have fewer corners (defensive)
match_importance_index     # knockout / high stakes = fewer corners
home_attack_strength       # shots per game home team (proxy for corner generation)
away_attack_strength
```

### Label Construction
```python
# From raw_matches table
label_corners_over = 1 if total_corners > 9.5 else 0
```

---

## Category 2 — Booking Markets (Target: Total Bookings O/U 3.5)

### Settlement Rules
- Yellow card = **1 booking**
- Red card / Yellow-Red card = **2 bookings**
- The 2nd yellow that causes a red is **NOT counted separately** (max 3 bookings per player)
- Cards for substituted players, managers, bench staff = **not counted**
- Cards after the final whistle = **not counted**
- Cards during the half-time break = counted as **2nd half cards**
- Regular time only

### Relevant Markets for Labelling

| Market | Description | Used For |
|---|---|---|
| **Total Bookings O/U** | Total bookings (Y=1, R=2) vs. line | **Primary label**: over/under 3.5 |
| **Total Booking Points O/U** | Total booking points (Y=10, R=25) vs. line | Secondary label / validation |
| **Booking 1X2** | Which team gets more bookings | Feature: booking aggression differential |
| **Home Team Total Bookings O/U** | Home team booking count vs. line | Feature: home team card rate |
| **Away Team Total Bookings O/U** | Away team booking count vs. line | Feature: away team card rate |
| **Sending Off** | Whether any player is sent off | Feature: red card probability |
| **Exact Bookings** | Exact number of bookings | Validation / distribution calibration |

### Features to Engineer

```python
# Rolling averages (last 5, 10 matches)
home_cards_per_game_avg       # yellow + (2 * red) per game, home team
away_cards_per_game_avg
home_fouls_per_game_avg       # fouls are a leading indicator for cards
away_fouls_per_game_avg

# Referee features (CRITICAL — referee is biggest predictor of card count)
referee_cards_per_game_avg    # average bookings issued by this referee
referee_red_rate              # red card frequency for this referee

# Match context
rivalry_index                 # H2H historical aggression level
is_derby                      # local derbies = more cards
match_stakes_index            # high-stakes matches = more tactical fouls
home_away_discipline_diff     # home_cards_avg - away_cards_avg
```

### Label Construction
```python
# booking_count = yellows + (2 * reds), per settlement rules
label_bookings_over = 1 if booking_count > 3.5 else 0
```

---

## Category 3 — GG/NG — Both Teams To Score (Target: BTTS Yes/No)

### Settlement Rules
- Settled at **regular time only**
- GG (Yes) = **both** teams score at least 1 goal
- NG (No) = at least one team fails to score
- Own goals count toward the team that conceded them (so they DO count for BTTS)
- Overtime not included

### Relevant Markets for Labelling

| Market | Description | Used For |
|---|---|---|
| **GG/NG** | Both teams score in regular time | **Primary label** |
| **1X2 & GG/NG** | Match result + BTTS | Compound validation |
| **1st Half GG/NG** | Both teams score in 1st half | Feature: first-half BTTS rate |
| **2nd Half GG/NG** | Both teams score in 2nd half | Feature: second-half BTTS rate |
| **Home Team Clean Sheet** | Home team concedes zero | Inverse BTTS signal |
| **Away Team Clean Sheet** | Away team concedes zero | Inverse BTTS signal |
| **Over/Under & GG/NG** | Goal total + BTTS combined | Compound validation |

### Features to Engineer

```python
# Team scoring rates (rolling 5, 10 matches)
home_scored_pct              # % of matches home team scored in
home_conceded_pct            # % of matches home team conceded in
away_scored_pct
away_conceded_pct

# Derived BTTS probability components
p_home_scores = home_scored_pct              # probability home team scores
p_away_scores = away_scored_pct              # probability away team scores
btts_base_prob = p_home_scores * p_away_scores  # naive independence estimate

# Defensive metrics
home_clean_sheet_rate        # % of home matches with zero goals conceded
away_clean_sheet_rate
home_goals_conceded_avg      # rolling average goals allowed
away_goals_conceded_avg

# Attacking metrics
home_goals_scored_avg
away_goals_scored_avg
home_xg_avg                  # expected goals (if available from source)
away_xg_avg

# Head-to-head
h2h_btts_rate                # % of H2H matches where both teams scored
```

### Label Construction
```python
label_btts = 1 if home_goals > 0 and away_goals > 0 else 0
```

---

## Category 4 — Asian Handicap (Target: Handicap Cover Yes/No)

### Settlement Rules
- Settled on **regular time only**
- Quarter-ball lines (0.25, 0.75, 1.25...): stake can be **half-won / half-lost**
- Half-ball lines (0.5, 1.5, 2.5...): **win or lose only**
- Whole-ball lines (0, 1, 2...): **win / lose / void** (void if exact margin = handicap)

| Handicap | Favoured Team Result | Outcome |
|---|---|---|
| -0.5 | Wins by any margin | Won |
| -0.5 | Draws or Loses | Lost |
| -1.0 | Wins by 2+ | Won |
| -1.0 | Wins by exactly 1 | **Void** |
| -1.0 | Draws or Loses | Lost |
| -1.5 | Wins by 2+ | Won |
| -1.5 | Wins by 1 or less | Lost |
| -0.25 | Wins | Won |
| -0.25 | Draws | **Half Lost** |
| -0.25 | Loses | Lost |
| +0.25 | Wins | Won |
| +0.25 | Draws | **Half Won** |
| +0.25 | Loses | Lost |

### Relevant Markets for Labelling

| Market | Description | Used For |
|---|---|---|
| **Asian Handicap** | Winner after handicap applied | **Primary label** |
| **Handicap** | Traditional handicap (European style) | Cross-validation |
| **1X2** | Match result without handicap | Feature: win probability baseline |
| **Draw No Bet** | Win/loss with draw voided | Feature: non-draw win rate |
| **Winning Margin** | Margin of victory | Feature / validation |

### Features to Engineer

```python
# Team strength
home_elo_rating              # Elo rating (computed rolling)
away_elo_rating
elo_differential             # home_elo - away_elo

# Form-based
home_win_rate_5              # win % in last 5 matches
away_win_rate_5
home_goals_scored_avg
away_goals_scored_avg
home_goals_conceded_avg
away_goals_conceded_avg

# Bookmaker signals (IMPORTANT — use market odds as features)
implied_prob_home            # 1 / home_odds (normalized)
implied_prob_away
implied_prob_draw
market_handicap_line         # the handicap line offered (e.g., -1.5, -0.5)

# Goal margin distributions
home_avg_margin_win          # average margin when home team wins
away_avg_margin_win
home_cover_rate_rolling      # % of matches home covered -0.5 handicap in last N games

# Context
home_advantage_factor        # historical home win % for this team's ground
is_neutral_venue             # World Cup knockout rounds often on neutral ground
```

### Label Construction
```python
# Example for -1.5 handicap on home team
goal_diff = home_goals - away_goals
if market_handicap == -1.5:
    label_handicap_cover = 1 if goal_diff >= 2 else 0
# Agent: implement full settlement logic for all handicap line types as per the table above
```

---

## Category 5 — Goals Over/Under (Target: Goals O/U 2.5)

### Settlement Rules
- Total goals = goals scored by both teams in **regular time + injury time only**
- Overtime and penalty shootout goals are **NOT counted**
- Over/Under line settlement:
  - **2.5 line:** ≤2 goals = Under wins; ≥3 goals = Over wins. No void possible.
  - **2.0 line:** <2 = Under; exactly 2 = **Void**; >2 = Over
  - **2.25 line:** <2 = Under wins fully; 2 goals = Half-win/Half-void; >2 = Over wins
  - **2.75 line:** ≤2 = Under wins fully; 3 goals = Half-win/Half-void; >3 = Over wins

### Relevant Markets for Labelling

| Market | Description | Used For |
|---|---|---|
| **Over/Under** | Total goals vs. line | **Primary label**: O/U 2.5 |
| **Home Team Over/Under** | Home goals vs. line | Feature: home scoring rate |
| **Away Team Over/Under** | Away goals vs. line | Feature: away scoring rate |
| **Exact Goals** | Exact goal total | Goal distribution modelling |
| **Goal Range** | Range bucket total goals fall into | Distribution calibration |
| **1st Half Over/Under** | First-half goals vs. line | Feature: first-half scoring pace |
| **Both Halves Over x.5** | Each half independently exceeds line | Compound signal |
| **Multigoals** | Range-based goal count prediction | Distribution validation |
| **Odd/Even Goals** | Parity of total goals | Supplementary market |
| **Home Team Clean Sheet** | Home concedes zero | Inverse scoring signal |
| **Away Team Clean Sheet** | Away concedes zero | Inverse scoring signal |
| **GG/NG** | Both teams score | Correlated signal — BTTS |

### Features to Engineer

```python
# Team scoring and conceding (rolling 5, 10 matches)
home_goals_scored_avg
home_goals_conceded_avg
away_goals_scored_avg
away_goals_conceded_avg

# Derived
total_goals_avg_combined    # home_scored + away_scored + home_conceded + away_conceded) / 2
                            # naive expected total goals
home_over25_rate            # % of home team's matches with 3+ total goals
away_over25_rate
h2h_goals_avg               # average goals in head-to-head history

# xG (if available)
home_xg_avg
away_xg_avg
combined_xg                 # home_xg + away_xg

# Bookmaker signals
implied_over_prob_25        # 1 / over_2.5_odds (if scraped)
implied_under_prob_25

# Context
match_importance_index      # knockout matches = fewer goals (risk aversion)
is_group_stage              # group stage = more open / more goals
climate_heat_index          # extreme heat affects pace and goal count
```

### Label Construction
```python
total_goals = home_goals + away_goals
label_goals_over25 = 1 if total_goals > 2.5 else 0
# i.e., label = 1 if total_goals >= 3
```

---

## 🛠️ Processed Features Table Schema

The agent must ensure the `processed_features` table in Supabase contains AT MINIMUM the following columns. Add columns as features are built — never remove existing ones.

```sql
CREATE TABLE processed_features (
    id                          SERIAL PRIMARY KEY,
    fixture_id                  TEXT NOT NULL REFERENCES wc_fixtures(id),
    created_at                  TIMESTAMPTZ DEFAULT NOW(),

    -- Team identifiers
    home_team                   TEXT,
    away_team                   TEXT,
    match_date                  DATE,

    -- === CORNER FEATURES ===
    home_corners_for_avg        FLOAT,
    home_corners_against_avg    FLOAT,
    away_corners_for_avg        FLOAT,
    away_corners_against_avg    FLOAT,
    total_corners_avg_combined  FLOAT,
    corner_dominance_home       FLOAT,
    is_cup_match                BOOLEAN,

    -- === BOOKING FEATURES ===
    home_cards_per_game_avg     FLOAT,
    away_cards_per_game_avg     FLOAT,
    home_fouls_per_game_avg     FLOAT,
    away_fouls_per_game_avg     FLOAT,
    referee_cards_per_game_avg  FLOAT,
    referee_red_rate            FLOAT,
    is_derby                    BOOLEAN,
    match_stakes_index          FLOAT,

    -- === BTTS FEATURES ===
    home_scored_pct             FLOAT,
    home_conceded_pct           FLOAT,
    away_scored_pct             FLOAT,
    away_conceded_pct           FLOAT,
    home_clean_sheet_rate       FLOAT,
    away_clean_sheet_rate       FLOAT,
    h2h_btts_rate               FLOAT,
    btts_base_prob              FLOAT,

    -- === HANDICAP FEATURES ===
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

    -- === GOALS FEATURES ===
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

    -- === SENTIMENT (optional) ===
    sentiment_score             FLOAT DEFAULT 0.0,

    -- === LABELS (populated after match completes) ===
    label_corners_over          SMALLINT,   -- 1 = over 9.5, 0 = under
    label_bookings_over         SMALLINT,   -- 1 = over 3.5, 0 = under
    label_btts                  SMALLINT,   -- 1 = yes, 0 = no
    label_handicap_cover        SMALLINT,   -- 1 = covered, 0 = not covered
    label_goals_over25          SMALLINT    -- 1 = over 2.5, 0 = under
);
```

---

## 🔁 Feature Engineering Pipeline — Required Functions

The agent must implement `src/features/feature_engineering.py` with the following functions:

```python
def compute_corner_features(fixture_id, historical_matches, window=10) -> dict:
    """Returns corner-related features for a given fixture."""

def compute_booking_features(fixture_id, historical_matches, referee_stats, window=10) -> dict:
    """Returns booking-related features. Referee data is mandatory."""

def compute_btts_features(fixture_id, historical_matches, h2h_matches, window=10) -> dict:
    """Returns BTTS features including H2H BTTS rate."""

def compute_handicap_features(fixture_id, historical_matches, elo_ratings, odds_data, window=5) -> dict:
    """Returns handicap features including Elo differential and implied probabilities."""

def compute_goals_features(fixture_id, historical_matches, h2h_matches, odds_data, window=10) -> dict:
    """Returns goals over/under features."""

def compute_labels(fixture_id, actual_result) -> dict:
    """
    Populates all label columns after a match completes.
    actual_result must contain: home_goals, away_goals, total_corners,
    total_yellow_cards, total_red_cards, handicap_line, handicap_team.
    Implements full Asian Handicap settlement logic as per rules above.
    """

def run_feature_pipeline(fixture_id) -> None:
    """
    Master function: calls all compute_*_features functions,
    merges results, and upserts into Supabase processed_features table.
    """
```

---

## ✅ Agent Checklist — Feature Engineering Tasks

When updating or building the feature engineering module, complete these in order:

- [ ] Implement `compute_corner_features()` with rolling window averages for home/away corner rates
- [ ] Implement `compute_booking_features()` — ensure referee lookup is included; if referee unknown, default to league average
- [ ] Implement `compute_btts_features()` including H2H BTTS rate and clean sheet rates
- [ ] Implement `compute_handicap_features()` including Elo rating computation and bookmaker implied probability extraction
- [ ] Implement `compute_goals_features()` including combined xG if available, else fall back to goals averages
- [ ] Implement `compute_labels()` with full Asian Handicap settlement logic for all line types (0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0)
- [ ] Implement `run_feature_pipeline()` as the master orchestrator
- [ ] Ensure all outputs upsert (not insert) to `processed_features` — re-runs must be idempotent
- [ ] Validate schema: all columns in the schema block above must exist before writing
- [ ] Handle missing data gracefully: if a team has <5 historical matches, use available data and flag `data_confidence = 'low'`
- [ ] Sentiment: if Reddit scraper fails or is unavailable, default `sentiment_score = 0.0` and continue — never block the pipeline

---

## 🚫 Out of Scope — Do Not Build Features For

The following SportyBet market categories exist but are **not prediction targets** for Sporty-Opele. Do not build features for them:

- Player markets (individual goalscorer, assists, shots, tackles, saves)
- Correct score markets
- Penalty shootout markets
- Overtime markets
- Next scoring type markets
- 1-minute or 5/10/15-minute interval markets
- Half Time / Full Time double result markets

---

*This document is part of the Sporty-Opele agent instruction set. Always read alongside `AGENT_INSTRUCTIONS.md`.*
*Last updated: June 2026*
