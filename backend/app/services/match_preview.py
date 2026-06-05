"""Orchestrator for the `/v1/match/{fixture_id}` endpoint.

Pulls together everything the match preview screen needs and returns a
sport-aware dict shaped for Flutter. Football and basketball have different
season-stat shapes and different supported feature subsets — this file
dispatches on the fixture's sport.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    BasketballTeamSeasonStats,
    Fixture,
    FootballTeamSeasonStats,
    League,
    Referee,
    Sport,
    Team,
)
from app.services.insights.generator import TrendInput, generate_insights
from app.services.referee.team_history import compute_referee_team_history
from app.services.stats.h2h import compute_h2h
from app.services.stats.hit_rate import compute_football_hit_rates
from app.services.stats.radar import basketball_radar, football_radar
from app.services.stats.trends import basketball_trend_series, football_trend_series


_FOOTBALL_TRENDS = ["goals_for", "goals_against", "corners", "yellow_cards", "shots_total"]
_BASKETBALL_TRENDS = ["points", "points_allowed", "rebounds_total", "assists", "three_made"]


async def build_match_preview(db: AsyncSession, fx: Fixture) -> dict:
    """Top-level dispatcher. Detects the league's sport and routes to
    football or basketball builder."""
    sport_code = await _sport_for_league(db, fx.league_id)
    home, away = await _load_teams(db, fx.home_team_id, fx.away_team_id)

    if sport_code == "basketball":
        return await _build_basketball(db, fx, home, away)
    return await _build_football(db, fx, home, away)


# =============================================================================
# Football
# =============================================================================

async def _build_football(db: AsyncSession, fx: Fixture, home: Team, away: Team) -> dict:
    referee = await _load_referee(db, fx.referee_id) if fx.referee_id else None

    home_stats = await _load_football_season_stats(db, fx.home_team_id, fx.league_id, fx.season_year)
    away_stats = await _load_football_season_stats(db, fx.away_team_id, fx.league_id, fx.season_year)

    home_hr = await compute_football_hit_rates(db, fx.home_team_id, fx.league_id, fx.season_year)
    away_hr = await compute_football_hit_rates(db, fx.away_team_id, fx.league_id, fx.season_year)
    home_hr_home = await compute_football_hit_rates(db, fx.home_team_id, fx.league_id, fx.season_year, home_only=True)
    away_hr_away = await compute_football_hit_rates(db, fx.away_team_id, fx.league_id, fx.season_year, away_only=True)

    home_trends = [
        await football_trend_series(db, fx.home_team_id, fx.league_id, fx.season_year, m)
        for m in _FOOTBALL_TRENDS
    ]
    away_trends = [
        await football_trend_series(db, fx.away_team_id, fx.league_id, fx.season_year, m)
        for m in _FOOTBALL_TRENDS
    ]

    radar = await football_radar(db, fx.home_team_id, fx.away_team_id, fx.league_id, fx.season_year)

    h2h = await compute_h2h(db, fx.home_team_id, fx.away_team_id, "football")

    referee_team_home = None
    referee_team_away = None
    if referee:
        referee_team_home = await compute_referee_team_history(db, referee.id, fx.home_team_id)
        referee_team_away = await compute_referee_team_history(db, referee.id, fx.away_team_id)

    home_trend_inputs = _football_trend_inputs(home_trends, home_stats)
    away_trend_inputs = _football_trend_inputs(away_trends, away_stats)
    insights = generate_insights(
        home_label=home.short_name or home.name,
        away_label=away.short_name or away.name,
        home_trends=home_trend_inputs,
        away_trends=away_trend_inputs,
        home_hit_rates={
            "over_25": home_hr.over_25_pct,
            "btts": home_hr.btts_pct,
            "corners_over_85": home_hr.corners_over_85_pct,
            "cards_over_35": home_hr.cards_over_35_pct,
        },
        away_hit_rates={
            "over_25": away_hr.over_25_pct,
            "btts": away_hr.btts_pct,
            "corners_over_85": away_hr.corners_over_85_pct,
            "cards_over_35": away_hr.cards_over_35_pct,
        },
    )

    return {
        "fixture": _fixture_payload(fx, sport="football"),
        "home": _football_team_payload(home, home_stats),
        "away": _football_team_payload(away, away_stats),
        "splits": {
            "home_team_at_home": _football_hr_payload(home_hr_home),
            "away_team_away": _football_hr_payload(away_hr_away),
        },
        "hit_rates": {
            "home_season": _football_hr_payload(home_hr),
            "away_season": _football_hr_payload(away_hr),
        },
        "radar": {"axes": radar.axes, "home": radar.home, "away": radar.away},
        "h2h": _h2h_payload(h2h),
        "trends": {
            "home": [_trend_payload(t) for t in home_trends],
            "away": [_trend_payload(t) for t in away_trends],
        },
        "referee": _referee_payload(referee, referee_team_home, referee_team_away),
        "insights": [
            {
                "rule": i.rule_code, "severity": i.severity,
                "headline": i.headline, "metric_key": i.metric_key,
                "metric_value": i.metric_value,
            }
            for i in insights
        ],
    }


# =============================================================================
# Basketball
# =============================================================================

async def _build_basketball(db: AsyncSession, fx: Fixture, home: Team, away: Team) -> dict:
    home_stats = await _load_basketball_season_stats(db, fx.home_team_id, fx.league_id, fx.season_year)
    away_stats = await _load_basketball_season_stats(db, fx.away_team_id, fx.league_id, fx.season_year)

    home_trends = [
        await basketball_trend_series(db, fx.home_team_id, fx.league_id, fx.season_year, m)
        for m in _BASKETBALL_TRENDS
    ]
    away_trends = [
        await basketball_trend_series(db, fx.away_team_id, fx.league_id, fx.season_year, m)
        for m in _BASKETBALL_TRENDS
    ]

    radar = await basketball_radar(db, fx.home_team_id, fx.away_team_id, fx.league_id, fx.season_year)

    h2h = await compute_h2h(db, fx.home_team_id, fx.away_team_id, "basketball")

    return {
        "fixture": _fixture_payload(fx, sport="basketball"),
        "home": _basketball_team_payload(home, home_stats),
        "away": _basketball_team_payload(away, away_stats),
        # Basketball doesn't carry these for v1; mobile renders conditionally.
        "splits": None,
        "hit_rates": None,
        "radar": {"axes": radar.axes, "home": radar.home, "away": radar.away},
        "h2h": _h2h_payload(h2h),
        "trends": {
            "home": [_trend_payload(t) for t in home_trends],
            "away": [_trend_payload(t) for t in away_trends],
        },
        "referee": None,
        "insights": [],
    }


# =============================================================================
# Shared helpers
# =============================================================================

async def _sport_for_league(db: AsyncSession, league_id: int) -> str:
    """Returns 'football' or 'basketball' (default football if unknown)."""
    row = (await db.execute(
        select(Sport.code).join(League, League.sport_id == Sport.id).where(League.id == league_id)
    )).scalar_one_or_none()
    return row or "football"


async def _load_teams(db: AsyncSession, home_id: int, away_id: int) -> tuple[Team, Team]:
    rows = (await db.execute(
        select(Team).where(Team.id.in_([home_id, away_id]))
    )).scalars().all()
    by_id = {t.id: t for t in rows}
    return by_id[home_id], by_id[away_id]


async def _load_referee(db: AsyncSession, referee_id: int) -> Optional[Referee]:
    return (await db.execute(
        select(Referee).where(Referee.id == referee_id)
    )).scalar_one_or_none()


async def _load_football_season_stats(
    db: AsyncSession, team_id: int, league_id: int, season: int
) -> Optional[FootballTeamSeasonStats]:
    return (await db.execute(
        select(FootballTeamSeasonStats).where(
            FootballTeamSeasonStats.team_id == team_id,
            FootballTeamSeasonStats.league_id == league_id,
            FootballTeamSeasonStats.season_year == season,
        )
    )).scalar_one_or_none()


async def _load_basketball_season_stats(
    db: AsyncSession, team_id: int, league_id: int, season: int
) -> Optional[BasketballTeamSeasonStats]:
    return (await db.execute(
        select(BasketballTeamSeasonStats).where(
            BasketballTeamSeasonStats.team_id == team_id,
            BasketballTeamSeasonStats.league_id == league_id,
            BasketballTeamSeasonStats.season_year == season,
        )
    )).scalar_one_or_none()


def _fixture_payload(fx: Fixture, *, sport: str) -> dict:
    return {
        "id": fx.id,
        "league_id": fx.league_id,
        "season": fx.season_year,
        "round": fx.round,
        "kickoff_at": fx.kickoff_at.isoformat(),
        "status": fx.status,
        "venue": fx.venue,
        "sport": sport,
    }


def _football_team_payload(team: Team, stats: Optional[FootballTeamSeasonStats]) -> dict:
    base = {"id": team.id, "name": team.name, "short_name": team.short_name, "logo": team.logo_url,
            "football_stats": None, "basketball_stats": None}
    if stats is None:
        return base
    base["football_stats"] = {
        "played": stats.played,
        "goals_for_pg": _f(stats.goals_for_pg),
        "goals_against_pg": _f(stats.goals_against_pg),
        "xg_pg": _f(stats.xg_pg),
        "shots_total_pg": _f(stats.shots_total_pg),
        "shots_on_pg": _f(stats.shots_on_pg),
        "corners_pg": _f(stats.corners_pg),
        "fouls_pg": _f(stats.fouls_pg),
        "offsides_pg": _f(stats.offsides_pg),
        "yellow_cards_pg": _f(stats.yellow_cards_pg),
        "red_cards_pg": _f(stats.red_cards_pg),
        "position": stats.position,
        "wins": stats.wins,
        "draws": stats.draws,
        "losses": stats.losses,
    }
    return base


def _basketball_team_payload(team: Team, stats: Optional[BasketballTeamSeasonStats]) -> dict:
    base = {"id": team.id, "name": team.name, "short_name": team.short_name, "logo": team.logo_url,
            "football_stats": None, "basketball_stats": None}
    if stats is None:
        return base
    base["basketball_stats"] = {
        "played": stats.played,
        "points_pg": _f(stats.points_pg),
        "points_allowed_pg": _f(stats.points_allowed_pg),
        "fg_pct": _f(stats.fg_pct),
        "two_pct": _f(stats.two_pct),
        "three_pct": _f(stats.three_pct),
        "ft_pct": _f(stats.ft_pct),
        "two_made_pg": _f(stats.two_made_pg),
        "two_att_pg": _f(stats.two_att_pg),
        "three_made_pg": _f(stats.three_made_pg),
        "three_att_pg": _f(stats.three_att_pg),
        "ft_made_pg": _f(stats.ft_made_pg),
        "ft_att_pg": _f(stats.ft_att_pg),
        "rebounds_off_pg": _f(stats.rebounds_off_pg),
        "rebounds_def_pg": _f(stats.rebounds_def_pg),
        "rebounds_total_pg": _f(stats.rebounds_total_pg),
        "assists_pg": _f(stats.assists_pg),
        "steals_pg": _f(stats.steals_pg),
        "blocks_pg": _f(stats.blocks_pg),
        "turnovers_pg": _f(stats.turnovers_pg),
        "home_played": stats.home_played,
        "home_points_pg": _f(stats.home_points_pg),
        "home_points_allowed_pg": _f(stats.home_points_allowed_pg),
        "away_played": stats.away_played,
        "away_points_pg": _f(stats.away_points_pg),
        "away_points_allowed_pg": _f(stats.away_points_allowed_pg),
        "wins": stats.wins,
        "losses": stats.losses,
    }
    return base


def _football_hr_payload(hr) -> dict:
    return {
        "matches": hr.matches,
        "over_15": hr.over_15_pct,
        "over_25": hr.over_25_pct,
        "over_35": hr.over_35_pct,
        "btts": hr.btts_pct,
        "corners_over_85": hr.corners_over_85_pct,
        "corners_over_105": hr.corners_over_105_pct,
        "cards_over_35": hr.cards_over_35_pct,
        "cards_over_45": hr.cards_over_45_pct,
    }


def _h2h_payload(h) -> Optional[dict]:
    if h is None or h.matches == 0:
        return None
    return {
        "matches": h.matches,
        "home_wins": h.home_wins,
        "away_wins": h.away_wins,
        "draws": h.draws,
        "avg_total": h.avg_total,
        "meetings": [
            {
                "date": m.date,
                "home_team_id": m.home_team_id,
                "away_team_id": m.away_team_id,
                "home_goals": m.home_goals,
                "away_goals": m.away_goals,
            }
            for m in h.meetings
        ],
    }


def _trend_payload(t) -> dict:
    return {
        "metric": t.metric,
        "values": t.values,
        "season_avg": t.season_avg,
        "delta_pct": t.delta_pct,
    }


def _referee_payload(referee: Optional[Referee], hist_home, hist_away) -> Optional[dict]:
    if referee is None:
        return None
    return {
        "id": referee.id,
        "name": referee.name,
        "nationality": referee.nationality,
        "photo": referee.photo_url,
        "vs_home_team": _hist_payload(hist_home),
        "vs_away_team": _hist_payload(hist_away),
    }


def _hist_payload(h) -> Optional[dict]:
    if h is None:
        return None
    return {
        "matches": h.matches,
        "yellow_cards_pg": h.yellow_cards_pg,
        "red_cards_pg": h.red_cards_pg,
        "fouls_pg": h.fouls_pg,
        "wins": h.wins, "draws": h.draws, "losses": h.losses,
    }


def _football_trend_inputs(trends, season_stats) -> list[TrendInput]:
    out = []
    if season_stats is None:
        return out
    lookup = {
        "goals_for": _f(season_stats.goals_for_pg),
        "goals_against": _f(season_stats.goals_against_pg),
        "corners": _f(season_stats.corners_pg),
        "yellow_cards": _f(season_stats.yellow_cards_pg),
        "shots_total": _f(season_stats.shots_total_pg),
    }
    for t in trends:
        if not t.values:
            continue
        avg = lookup.get(t.metric)
        if avg is None:
            continue
        out.append(TrendInput(
            metric=t.metric,
            last_avg=sum(t.values) / len(t.values),
            season_avg=avg,
            last_n=len(t.values),
        ))
    return out


def _f(x) -> Optional[float]:
    return float(x) if x is not None else None
