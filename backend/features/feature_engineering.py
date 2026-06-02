"""
Feature engineering for Sporty-Opele prediction markets.
See .agents/rules/feature_eng.md for market definitions and schema.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from typing import Any, Optional

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db.supabase_client import supabase

# Defaults when historical / referee / odds data is missing
DEFAULT_ELO = 1500.0
LEAGUE_AVG_BOOKINGS = 4.0
LEAGUE_RED_RATE = 0.10
DEFAULT_HANDICAP_LINE = -0.5
MIN_MATCHES_FOR_HIGH_CONFIDENCE = 5

PROCESSED_FEATURES_COLUMNS = [
    "fixture_id",
    "home_team",
    "away_team",
    "match_date",
    "home_corners_for_avg",
    "home_corners_against_avg",
    "away_corners_for_avg",
    "away_corners_against_avg",
    "total_corners_avg_combined",
    "corner_dominance_home",
    "is_cup_match",
    "home_cards_per_game_avg",
    "away_cards_per_game_avg",
    "home_fouls_per_game_avg",
    "away_fouls_per_game_avg",
    "referee_cards_per_game_avg",
    "referee_red_rate",
    "is_derby",
    "match_stakes_index",
    "home_scored_pct",
    "home_conceded_pct",
    "away_scored_pct",
    "away_conceded_pct",
    "home_clean_sheet_rate",
    "away_clean_sheet_rate",
    "h2h_btts_rate",
    "btts_base_prob",
    "home_elo_rating",
    "away_elo_rating",
    "elo_differential",
    "home_win_rate_5",
    "away_win_rate_5",
    "implied_prob_home",
    "implied_prob_away",
    "implied_prob_draw",
    "market_handicap_line",
    "home_cover_rate_rolling",
    "is_neutral_venue",
    "home_goals_scored_avg",
    "home_goals_conceded_avg",
    "away_goals_scored_avg",
    "away_goals_conceded_avg",
    "total_goals_avg_combined",
    "home_over25_rate",
    "away_over25_rate",
    "h2h_goals_avg",
    "home_xg_avg",
    "away_xg_avg",
    "combined_xg",
    "implied_over_prob_25",
    "match_importance_index",
    "is_group_stage",
    "sentiment_score",
    "data_confidence",
    "label_corners_over",
    "label_bookings_over",
    "label_btts",
    "label_handicap_cover",
    "label_goals_over25",
]


def _safe_mean(values: list[float], default: float = 0.0) -> float:
    if not values:
        return default
    return sum(values) / len(values)


def _rolling(values: list[float], window: int) -> list[float]:
    if not values:
        return []
    return values[-window:]


def _parse_date(match_date: Any) -> date:
    if isinstance(match_date, date):
        return match_date
    return date.fromisoformat(str(match_date)[:10])


def fetch_fixture(fixture_id: int) -> Optional[dict]:
    rows = supabase.table("wc_fixtures").select("*").eq("id", fixture_id).execute().data
    return rows[0] if rows else None


def fetch_all_fixtures() -> list[dict]:
    return supabase.table("wc_fixtures").select("*").execute().data or []


def fetch_completed_fixtures(before_date: Optional[date] = None) -> list[dict]:
    fixtures = [
        f
        for f in fetch_all_fixtures()
        if f.get("match_completed")
        and f.get("result_home_goals") is not None
    ]
    if before_date:
        fixtures = [f for f in fixtures if _parse_date(f["match_date"]) < before_date]
    fixtures.sort(key=lambda f: _parse_date(f["match_date"]))
    return fixtures


def get_team_features(team_name: str) -> dict:
    """Fetch a team's aggregate stats from wc_teams."""
    result = supabase.table("wc_teams").select("*").eq("team_name", team_name).execute()
    if not result.data:
        return {}
    row = result.data[0]
    return {
        "ppg": row.get("ppg", 0) or 0.0,
        "xg": row.get("xg", 0) or 0.0,
        "xga": row.get("xga", 0) or 0.0,
        "btts_pct": (row.get("btts_pct", 0) or 0.0) / 100.0,
        "clean_sheet_pct": (row.get("clean_sheet_pct", 0) or 0.0) / 100.0,
        "avg_corners": row.get("avg_corners", 0) or 0.0,
        "avg_cards": row.get("avg_cards", 0) or 0.0,
        "avg_goals": row.get("avg_goals", 0) or 0.0,
        "over_25_pct": (row.get("over_25_pct", 0) or 0.0) / 100.0,
        "sentiment_score": row.get("sentiment_score", 0) or 0.0,
    }


def _team_perspective(match: dict, team: str) -> Optional[dict]:
    """Per-team stats from a single completed fixture."""
    home = match["home_team"]
    away = match["away_team"]
    hg = match.get("result_home_goals")
    ag = match.get("result_away_goals")
    hc = match.get("result_home_corners")
    ac = match.get("result_away_corners")
    cards = match.get("result_total_cards")
    if hg is None or ag is None:
        return None

    if team == home:
        return {
            "goals_for": hg,
            "goals_against": ag,
            "corners_for": hc or 0,
            "corners_against": ac or 0,
            "cards": (cards or 0) / 2.0,
            "scored": hg > 0,
            "conceded": ag > 0,
            "clean_sheet": ag == 0,
            "over25": (hg + ag) > 2.5,
            "won": hg > ag,
            "drew": hg == ag,
            "margin": hg - ag,
            "is_home": True,
        }
    if team == away:
        return {
            "goals_for": ag,
            "goals_against": hg,
            "corners_for": ac or 0,
            "corners_against": hc or 0,
            "cards": (cards or 0) / 2.0,
            "scored": ag > 0,
            "conceded": hg > 0,
            "clean_sheet": hg == 0,
            "over25": (hg + ag) > 2.5,
            "won": ag > hg,
            "drew": hg == ag,
            "margin": ag - hg,
            "is_home": False,
        }
    return None


def _matches_for_team(team: str, historical_matches: list[dict]) -> list[dict]:
    return [m for m in historical_matches if team in (m["home_team"], m["away_team"])]


def _h2h_matches(home: str, away: str, historical_matches: list[dict]) -> list[dict]:
    return [
        m
        for m in historical_matches
        if {m["home_team"], m["away_team"]} == {home, away}
    ]


def _data_confidence(team_matches: list[dict], window: int) -> str:
    n = len(team_matches)
    if n < MIN_MATCHES_FOR_HIGH_CONFIDENCE:
        return "low"
    if n < window:
        return "medium"
    return "high"


def compute_elo_ratings(historical_matches: list[dict], k: float = 20.0) -> dict[str, float]:
    """Rolling Elo from completed fixtures in chronological order."""
    ratings: dict[str, float] = {}

    def get(team: str) -> float:
        return ratings.setdefault(team, DEFAULT_ELO)

    for match in historical_matches:
        home, away = match["home_team"], match["away_team"]
        hg, ag = match.get("result_home_goals"), match.get("result_away_goals")
        if hg is None or ag is None:
            continue

        rh, ra = get(home), get(away)
        exp_home = 1.0 / (1.0 + 10 ** ((ra - rh) / 400))
        if hg > ag:
            score_home = 1.0
        elif hg < ag:
            score_home = 0.0
        else:
            score_home = 0.5

        ratings[home] = rh + k * (score_home - exp_home)
        ratings[away] = ra + k * ((1 - score_home) - (1 - exp_home))

    return ratings


def settle_asian_handicap(
    home_goals: int,
    away_goals: int,
    handicap_line: float,
    side: str = "home",
) -> Optional[int]:
    """
    Binary cover label for training (1=cover, 0=no cover, None=void).
    Quarter-ball lines: half-won -> 1, half-lost -> 0.
    """
    goal_diff = home_goals - away_goals
    margin = goal_diff if side == "home" else -goal_diff
    line = handicap_line if side == "home" else -handicap_line

    def half_ball_result(adj_line: float) -> int:
        adj = margin + adj_line
        if adj > 0:
            return 1
        if adj < 0:
            return 0
        return 0  # push on integer half-lines treated as no cover for binary

    frac = abs(line) % 1
    if abs(frac - 0.25) < 1e-9 or abs(frac - 0.75) < 1e-9:
        low = half_ball_result(line - 0.25)
        high = half_ball_result(line + 0.25)
        if low == 1 and high == 1:
            return 1
        if low == 0 and high == 0:
            return 0
        return 1 if (low + high) >= 1 else 0

    adj = margin + line
    whole = abs(line) % 1 < 1e-9
    if whole and abs(adj) < 1e-9:
        return None
    return 1 if adj > 0 else 0


def compute_corner_features(
    fixture_id: int,
    historical_matches: list[dict],
    window: int = 10,
) -> dict:
    fixture = fetch_fixture(fixture_id)
    if not fixture:
        return {}

    home, away = fixture["home_team"], fixture["away_team"]
    home_hist = _matches_for_team(home, historical_matches)
    away_hist = _matches_for_team(away, historical_matches)

    def corner_avgs(team: str, matches: list[dict]) -> tuple[float, float]:
        for_vals, against_vals = [], []
        for m in _rolling(matches, window):
            p = _team_perspective(m, team)
            if p:
                for_vals.append(p["corners_for"])
                against_vals.append(p["corners_against"])
        home_stats = get_team_features(team)
        return (
            _safe_mean(for_vals, home_stats.get("avg_corners", 5.0) / 2),
            _safe_mean(against_vals, home_stats.get("avg_corners", 5.0) / 2),
        )

    hf, ha = corner_avgs(home, home_hist)
    af, aa = corner_avgs(away, away_hist)
    total_combined = (hf + af + ha + aa) / 2.0
    denom = hf + af
    dominance = hf / denom if denom > 0 else 0.5

    stage = (fixture.get("stage") or "").lower()
    is_cup = "group" not in stage and stage not in ("", "historical")

    return {
        "home_corners_for_avg": round(hf, 4),
        "home_corners_against_avg": round(ha, 4),
        "away_corners_for_avg": round(af, 4),
        "away_corners_against_avg": round(aa, 4),
        "total_corners_avg_combined": round(total_combined, 4),
        "corner_dominance_home": round(dominance, 4),
        "is_cup_match": is_cup,
        "match_importance_index": 1.0 if "knockout" in stage or "final" in stage else 0.3,
    }


def compute_booking_features(
    fixture_id: int,
    historical_matches: list[dict],
    referee_stats: Optional[dict] = None,
    window: int = 10,
) -> dict:
    fixture = fetch_fixture(fixture_id)
    if not fixture:
        return {}

    home, away = fixture["home_team"], fixture["away_team"]
    ref = referee_stats or {}
    ref_cards = ref.get("cards_per_game_avg", LEAGUE_AVG_BOOKINGS)
    ref_red = ref.get("red_rate", LEAGUE_RED_RATE)

    def card_avgs(team: str) -> tuple[float, float]:
        cards, fouls = [], []
        matches = _rolling(_matches_for_team(team, historical_matches), window)
        for m in matches:
            p = _team_perspective(m, team)
            if p:
                cards.append(p["cards"])
                fouls.append(p["cards"] * 2.5)  # proxy when fouls not in data
        t = get_team_features(team)
        return _safe_mean(cards, t.get("avg_cards", 3.0)), _safe_mean(fouls, t.get("avg_cards", 3.0) * 2.5)

    hc, hf = card_avgs(home)
    ac, af = card_avgs(away)

    h2h = _h2h_matches(home, away, historical_matches)
    h2h_cards = [
        m.get("result_total_cards", 0) or 0 for m in h2h if m.get("result_total_cards") is not None
    ]
    rivalry = _safe_mean(h2h_cards, LEAGUE_AVG_BOOKINGS) / LEAGUE_AVG_BOOKINGS

    stage = (fixture.get("stage") or "").lower()
    stakes = 1.0 if "knockout" in stage or "final" in stage else 0.5

    return {
        "home_cards_per_game_avg": round(hc, 4),
        "away_cards_per_game_avg": round(ac, 4),
        "home_fouls_per_game_avg": round(hf, 4),
        "away_fouls_per_game_avg": round(af, 4),
        "referee_cards_per_game_avg": round(ref_cards, 4),
        "referee_red_rate": round(ref_red, 4),
        "is_derby": False,
        "match_stakes_index": round(stakes, 4),
        "rivalry_index": round(rivalry, 4),
        "home_away_discipline_diff": round(hc - ac, 4),
    }


def compute_btts_features(
    fixture_id: int,
    historical_matches: list[dict],
    h2h_matches: list[dict],
    window: int = 10,
) -> dict:
    fixture = fetch_fixture(fixture_id)
    if not fixture:
        return {}

    home, away = fixture["home_team"], fixture["away_team"]

    def rates(team: str) -> tuple[float, float, float]:
        scored, conceded, clean = [], [], []
        for m in _rolling(_matches_for_team(team, historical_matches), window):
            p = _team_perspective(m, team)
            if p:
                scored.append(1.0 if p["scored"] else 0.0)
                conceded.append(1.0 if p["conceded"] else 0.0)
                clean.append(1.0 if p["clean_sheet"] else 0.0)
        t = get_team_features(team)
        sp = _safe_mean(scored, t.get("btts_pct", 0.5))
        cp = _safe_mean(conceded, 1.0 - t.get("clean_sheet_pct", 0.5))
        cs = _safe_mean(clean, t.get("clean_sheet_pct", 0.5))
        return sp, cp, cs

    h_sp, h_cp, h_cs = rates(home)
    a_sp, a_cp, a_cs = rates(away)

    h2h_btts = []
    for m in h2h_matches:
        hg, ag = m.get("result_home_goals"), m.get("result_away_goals")
        if hg is not None and ag is not None:
            h2h_btts.append(1.0 if hg > 0 and ag > 0 else 0.0)
    h2h_rate = _safe_mean(h2h_btts, (h_sp + a_sp) / 2)

    return {
        "home_scored_pct": round(h_sp, 4),
        "home_conceded_pct": round(h_cp, 4),
        "away_scored_pct": round(a_sp, 4),
        "away_conceded_pct": round(a_cp, 4),
        "home_clean_sheet_rate": round(h_cs, 4),
        "away_clean_sheet_rate": round(a_cs, 4),
        "h2h_btts_rate": round(h2h_rate, 4),
        "btts_base_prob": round(h_sp * a_sp, 4),
    }


def compute_handicap_features(
    fixture_id: int,
    historical_matches: list[dict],
    elo_ratings: dict[str, float],
    odds_data: Optional[dict] = None,
    window: int = 5,
) -> dict:
    fixture = fetch_fixture(fixture_id)
    if not fixture:
        return {}

    home, away = fixture["home_team"], fixture["away_team"]
    odds = odds_data or {}

    def win_rate(team: str) -> float:
        wins = []
        for m in _rolling(_matches_for_team(team, historical_matches), window):
            p = _team_perspective(m, team)
            if p:
                wins.append(1.0 if p["won"] else 0.0)
        return _safe_mean(wins, get_team_features(team).get("ppg", 1.5) / 3.0)

    def cover_rate(team: str) -> float:
        covers = []
        for m in _rolling(_matches_for_team(team, historical_matches), window):
            p = _team_perspective(m, team)
            if not p:
                continue
            hg, ag = m.get("result_home_goals"), m.get("result_away_goals")
            if hg is None or ag is None:
                continue
            side = "home" if team == m["home_team"] else "away"
            label = settle_asian_handicap(hg, ag, DEFAULT_HANDICAP_LINE, side=side)
            if label is not None:
                covers.append(float(label))
        return _safe_mean(covers, 0.5)

    home_elo = elo_ratings.get(home, DEFAULT_ELO)
    away_elo = elo_ratings.get(away, DEFAULT_ELO)

    implied_home = odds.get("implied_prob_home")
    implied_away = odds.get("implied_prob_away")
    implied_draw = odds.get("implied_prob_draw")

    stage = (fixture.get("stage") or "").lower()
    neutral = "knockout" in stage and "quarter" in stage

    return {
        "home_elo_rating": round(home_elo, 2),
        "away_elo_rating": round(away_elo, 2),
        "elo_differential": round(home_elo - away_elo, 2),
        "home_win_rate_5": round(win_rate(home), 4),
        "away_win_rate_5": round(win_rate(away), 4),
        "implied_prob_home": implied_home,
        "implied_prob_away": implied_away,
        "implied_prob_draw": implied_draw,
        "market_handicap_line": odds.get("market_handicap_line", DEFAULT_HANDICAP_LINE),
        "home_cover_rate_rolling": round(cover_rate(home), 4),
        "is_neutral_venue": neutral,
    }


def compute_goals_features(
    fixture_id: int,
    historical_matches: list[dict],
    h2h_matches: list[dict],
    odds_data: Optional[dict] = None,
    window: int = 10,
) -> dict:
    fixture = fetch_fixture(fixture_id)
    if not fixture:
        return {}

    home, away = fixture["home_team"], fixture["away_team"]
    odds = odds_data or {}

    def goal_avgs(team: str) -> tuple[float, float, float]:
        scored, conceded, over25 = [], [], []
        for m in _rolling(_matches_for_team(team, historical_matches), window):
            p = _team_perspective(m, team)
            if p:
                scored.append(p["goals_for"])
                conceded.append(p["goals_against"])
                over25.append(1.0 if p["over25"] else 0.0)
        t = get_team_features(team)
        return (
            _safe_mean(scored, t.get("avg_goals", 1.3)),
            _safe_mean(conceded, t.get("avg_goals", 1.3)),
            _safe_mean(over25, t.get("over_25_pct", 0.5)),
        )

    h_gs, h_gc, h_o25 = goal_avgs(home)
    a_gs, a_gc, a_o25 = goal_avgs(away)
    total_combined = (h_gs + a_gs + h_gc + a_gc) / 2.0

    h2h_goals = []
    for m in h2h_matches:
        hg, ag = m.get("result_home_goals"), m.get("result_away_goals")
        if hg is not None and ag is not None:
            h2h_goals.append(hg + ag)
    h2h_avg = _safe_mean(h2h_goals, total_combined)

    ht, at = get_team_features(home), get_team_features(away)
    home_xg = ht.get("xg", 1.2)
    away_xg = at.get("xg", 1.2)

    stage = (fixture.get("stage") or "").lower()
    is_group = "group" in stage

    return {
        "home_goals_scored_avg": round(h_gs, 4),
        "home_goals_conceded_avg": round(h_gc, 4),
        "away_goals_scored_avg": round(a_gs, 4),
        "away_goals_conceded_avg": round(a_gc, 4),
        "total_goals_avg_combined": round(total_combined, 4),
        "home_over25_rate": round(h_o25, 4),
        "away_over25_rate": round(a_o25, 4),
        "h2h_goals_avg": round(h2h_avg, 4),
        "home_xg_avg": round(home_xg, 4),
        "away_xg_avg": round(away_xg, 4),
        "combined_xg": round(home_xg + away_xg, 4),
        "implied_over_prob_25": odds.get("implied_over_prob_25"),
        "match_importance_index": 1.0 if "knockout" in stage else 0.3,
        "is_group_stage": is_group,
    }


def compute_labels(fixture_id: int, actual_result: dict) -> dict:
    """
    Populate label columns after a match completes.
    actual_result: home_goals, away_goals, total_corners (or home/away corners),
    total_yellow_cards, total_red_cards (or booking_count), handicap_line, handicap_team.
    """
    hg = int(actual_result["home_goals"])
    ag = int(actual_result["away_goals"])

    if "total_corners" in actual_result:
        total_corners = int(actual_result["total_corners"])
    else:
        total_corners = int(actual_result.get("home_corners", 0)) + int(
            actual_result.get("away_corners", 0)
        )

    if "booking_count" in actual_result:
        booking_count = float(actual_result["booking_count"])
    else:
        yc = int(actual_result.get("total_yellow_cards", 0))
        rc = int(actual_result.get("total_red_cards", 0))
        booking_count = yc + 2 * rc
        if booking_count == 0 and actual_result.get("result_total_cards") is not None:
            booking_count = float(actual_result["result_total_cards"])

    handicap_line = float(actual_result.get("handicap_line", DEFAULT_HANDICAP_LINE))
    handicap_team = actual_result.get("handicap_team", "home")
    side = "home" if handicap_team == "home" else "away"

    total_goals = hg + ag
    handicap_label = settle_asian_handicap(hg, ag, handicap_line, side=side)

    labels = {
        "label_corners_over": 1 if total_corners > 9.5 else 0,
        "label_bookings_over": 1 if booking_count > 3.5 else 0,
        "label_btts": 1 if hg > 0 and ag > 0 else 0,
        "label_goals_over25": 1 if total_goals > 2.5 else 0,
    }
    if handicap_label is not None:
        labels["label_handicap_cover"] = handicap_label
    return labels


def _sentiment_for_fixture(home: str, away: str) -> float:
    try:
        h = get_team_features(home).get("sentiment_score", 0.0)
        a = get_team_features(away).get("sentiment_score", 0.0)
        return round((h + a) / 2.0, 4)
    except Exception:
        return 0.0


def run_feature_pipeline(fixture_id: int) -> None:
    """Compute all features and upsert into processed_features."""
    fixture = fetch_fixture(fixture_id)
    if not fixture:
        print(f"  ✗ Fixture {fixture_id} not found")
        return

    match_date = _parse_date(fixture["match_date"])
    historical = fetch_completed_fixtures(before_date=match_date)
    home, away = fixture["home_team"], fixture["away_team"]
    h2h = _h2h_matches(home, away, historical)
    elo = compute_elo_ratings(historical)

    row: dict[str, Any] = {
        "fixture_id": fixture_id,
        "home_team": home,
        "away_team": away,
        "match_date": str(match_date),
        "sentiment_score": _sentiment_for_fixture(home, away),
    }

    row.update(compute_corner_features(fixture_id, historical))
    row.update(compute_booking_features(fixture_id, historical))
    row.update(compute_btts_features(fixture_id, historical, h2h))
    row.update(compute_handicap_features(fixture_id, historical, elo))
    row.update(compute_goals_features(fixture_id, historical, h2h))

    n_home = len(_matches_for_team(home, historical))
    n_away = len(_matches_for_team(away, historical))
    row["data_confidence"] = (
        "low"
        if n_home < MIN_MATCHES_FOR_HIGH_CONFIDENCE or n_away < MIN_MATCHES_FOR_HIGH_CONFIDENCE
        else "high"
    )

    if fixture.get("match_completed"):
        actual = {
            "home_goals": fixture.get("result_home_goals", 0),
            "away_goals": fixture.get("result_away_goals", 0),
            "home_corners": fixture.get("result_home_corners", 0),
            "away_corners": fixture.get("result_away_corners", 0),
            "result_total_cards": fixture.get("result_total_cards"),
            "handicap_line": DEFAULT_HANDICAP_LINE,
            "handicap_team": "home",
        }
        row.update(compute_labels(fixture_id, actual))

    supabase.table("processed_features").upsert(row, on_conflict="fixture_id").execute()
    print(f"  ✓ processed_features upserted for fixture {fixture_id} ({home} vs {away})")


def run_feature_pipeline_all() -> int:
    """Run feature pipeline for every fixture in wc_fixtures."""
    fixtures = fetch_all_fixtures()
    print(f"Running feature pipeline for {len(fixtures)} fixtures...")
    for f in fixtures:
        run_feature_pipeline(f["id"])
    return len(fixtures)


def get_processed_features(fixture_id: int) -> Optional[dict]:
    rows = (
        supabase.table("processed_features")
        .select("*")
        .eq("fixture_id", fixture_id)
        .execute()
        .data
    )
    return rows[0] if rows else None


def build_match_features(home_team: str, away_team: str, fixture_id: Optional[int] = None) -> pd.DataFrame:
    """
    Build a single-row DataFrame for model.predict().
    Uses processed_features when available; otherwise team aggregates.
    """
    pf = None
    if fixture_id is not None:
        pf = get_processed_features(fixture_id)
    if pf is None:
        all_fixtures = fetch_all_fixtures()
        for f in all_fixtures:
            if f["home_team"] == home_team and f["away_team"] == away_team:
                pf = get_processed_features(f["id"])
                if pf:
                    break

    home = get_team_features(home_team)
    away = get_team_features(away_team)
    if not home or not away:
        raise ValueError(f"Missing team data for {home_team} or {away_team}")

    if pf:
        home_corners = pf.get("home_corners_for_avg", home["avg_corners"] / 2)
        away_corners = pf.get("away_corners_for_avg", away["avg_corners"] / 2)
        total_corners = pf.get("total_corners_avg_combined", home_corners + away_corners)
        home_cards = pf.get("home_cards_per_game_avg", home["avg_cards"])
        away_cards = pf.get("away_cards_per_game_avg", away["avg_cards"])
        btts_combined = pf.get("btts_base_prob", (home["btts_pct"] + away["btts_pct"]) / 2)
        sentiment = pf.get("sentiment_score", 0.0)
    else:
        home_corners = home["avg_corners"] / 2
        away_corners = away["avg_corners"] / 2
        total_corners = home["avg_corners"] + away["avg_corners"]
        home_cards = home["avg_cards"]
        away_cards = away["avg_cards"]
        btts_combined = (home["btts_pct"] + away["btts_pct"]) / 2
        sentiment = (home["sentiment_score"] + away["sentiment_score"]) / 2

    features = {
        "home_ppg": home["ppg"],
        "home_xg": home["xg"],
        "home_xga": home["xga"],
        "home_btts_pct": home["btts_pct"],
        "home_clean_sheet_pct": home["clean_sheet_pct"],
        "home_avg_corners": home_corners,
        "home_avg_cards": home_cards,
        "home_avg_goals": home["avg_goals"],
        "home_over_25_pct": home["over_25_pct"],
        "home_sentiment": home["sentiment_score"],
        "away_ppg": away["ppg"],
        "away_xg": away["xg"],
        "away_xga": away["xga"],
        "away_btts_pct": away["btts_pct"],
        "away_clean_sheet_pct": away["clean_sheet_pct"],
        "away_avg_corners": away_corners,
        "away_avg_cards": away_cards,
        "away_avg_goals": away["avg_goals"],
        "away_over_25_pct": away["over_25_pct"],
        "away_sentiment": away["sentiment_score"],
        "total_avg_corners": total_corners,
        "total_avg_cards": home_cards + away_cards,
        "total_avg_goals": home["avg_goals"] + away["avg_goals"],
        "btts_combined": btts_combined,
        "sentiment_delta": home["sentiment_score"] - away["sentiment_score"],
    }

    return pd.DataFrame([features])


if __name__ == "__main__":
    count = run_feature_pipeline_all()
    print(f"\nDone. Processed {count} fixtures.")
