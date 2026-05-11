"""Trend graphs: last-N values per stat, with the season average as a baseline.

Drives the line-chart cards in the match preview ("son 10 maç" eğrisi vs
sezon ortalaması line'ı). Returns plain dicts ready to ship to Flutter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BasketballFixtureTeamStats, Fixture, FootballFixtureTeamStats


@dataclass
class TrendSeries:
    metric: str             # 'goals_for' / 'corners' / 'yellow_cards' / ...
    values: list[float]     # most recent first → reverse before charting
    season_avg: Optional[float]
    delta_pct: Optional[float]   # how this team's last-N avg compares to season avg


async def football_trend_series(
    db: AsyncSession,
    team_id: int,
    league_id: int,
    season: int,
    metric: str,
    last_n: int = 10,
) -> TrendSeries:
    """Return last-N values of `metric` for `team_id` in (league, season)."""
    fxs = Fixture
    ts = FootballFixtureTeamStats

    value_expr = _metric_expression(metric, team_id, fxs, ts)
    if value_expr is None:
        return TrendSeries(metric=metric, values=[], season_avg=None, delta_pct=None)

    is_team = (fxs.home_team_id == team_id) | (fxs.away_team_id == team_id)

    stmt = (
        select(value_expr.label("v"))
        .select_from(
            fxs.__table__.outerjoin(ts.__table__, (ts.fixture_id == fxs.id) & (ts.team_id == team_id))
        )
        .where(
            fxs.league_id == league_id,
            fxs.season_year == season,
            fxs.is_finished.is_(True),
            is_team,
        )
        .order_by(fxs.kickoff_at.desc())
        .limit(last_n)
    )

    rows = (await db.execute(stmt)).all()
    values = [float(r.v) for r in rows if r.v is not None]

    if not values:
        return TrendSeries(metric=metric, values=[], season_avg=None, delta_pct=None)

    season_avg = round(sum(values) / len(values), 2)
    last_avg = season_avg  # placeholder until we wire team_season_stats lookup
    delta_pct = None

    return TrendSeries(
        metric=metric,
        values=values,
        season_avg=season_avg,
        delta_pct=delta_pct,
    )


def _metric_expression(metric: str, team_id: int, fxs, ts):
    """Map a metric name to a SQL expression for the team's per-match value."""
    is_home = fxs.home_team_id == team_id
    if metric == "goals_for":
        return case((is_home, fxs.home_goals), else_=fxs.away_goals)
    if metric == "goals_against":
        return case((is_home, fxs.away_goals), else_=fxs.home_goals)
    if metric == "corners":
        return ts.corners
    if metric == "yellow_cards":
        return ts.yellow_cards
    if metric == "shots_total":
        return ts.shots_total
    if metric == "shots_on":
        return ts.shots_on
    if metric == "fouls":
        return ts.fouls
    return None


# --- Basketball ---

async def basketball_trend_series(
    db: AsyncSession,
    team_id: int,
    league_id: int,
    season: int,
    metric: str,
    last_n: int = 10,
) -> TrendSeries:
    """Last-N values of `metric` for `team_id` in basketball."""
    fxs = Fixture
    ts = BasketballFixtureTeamStats

    value_expr = _bbball_metric_expr(metric, team_id, fxs, ts)
    if value_expr is None:
        return TrendSeries(metric=metric, values=[], season_avg=None, delta_pct=None)

    is_team = (fxs.home_team_id == team_id) | (fxs.away_team_id == team_id)

    stmt = (
        select(value_expr.label("v"))
        .select_from(
            fxs.__table__.outerjoin(ts.__table__, (ts.fixture_id == fxs.id) & (ts.team_id == team_id))
        )
        .where(
            fxs.league_id == league_id,
            fxs.season_year == season,
            fxs.is_finished.is_(True),
            is_team,
        )
        .order_by(fxs.kickoff_at.desc())
        .limit(last_n)
    )

    rows = (await db.execute(stmt)).all()
    values = [float(r.v) for r in rows if r.v is not None]
    if not values:
        return TrendSeries(metric=metric, values=[], season_avg=None, delta_pct=None)

    season_avg = round(sum(values) / len(values), 2)
    return TrendSeries(metric=metric, values=values, season_avg=season_avg, delta_pct=None)


def _bbball_metric_expr(metric: str, team_id: int, fxs, ts):
    is_home = fxs.home_team_id == team_id
    if metric == "points":
        return case((is_home, fxs.home_goals), else_=fxs.away_goals)
    if metric == "points_allowed":
        return case((is_home, fxs.away_goals), else_=fxs.home_goals)
    if metric == "rebounds_total":
        return ts.rebounds_offensive + ts.rebounds_defensive
    if metric == "assists":
        return ts.assists
    if metric == "three_made":
        return ts.three_points_made
    return None
