"""Hakem × Takım eşleşmesi — historical matchups between a referee and a team.

For a given (referee, team) pair, compute averages and win/draw/loss split
across every fixture this ref officiated for this team across all leagues
and seasons we have. Returned to the match preview when a referee is
assigned.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Fixture, FootballFixtureTeamStats


@dataclass
class RefereeTeamHistory:
    matches: int
    yellow_cards_pg: Optional[float]
    red_cards_pg: Optional[float]
    fouls_pg: Optional[float]
    wins: int
    draws: int
    losses: int


_MIN_SAMPLES = 2


async def compute_referee_team_history(
    db: AsyncSession,
    referee_id: int,
    team_id: int,
) -> RefereeTeamHistory:
    fxs = Fixture
    ts = FootballFixtureTeamStats

    is_team = (fxs.home_team_id == team_id) | (fxs.away_team_id == team_id)
    is_home = fxs.home_team_id == team_id

    # Win/draw/loss from this team's perspective
    win = case(
        (is_home & (fxs.home_goals > fxs.away_goals), 1),
        (~is_home & (fxs.away_goals > fxs.home_goals), 1),
        else_=0,
    )
    draw = case((fxs.home_goals == fxs.away_goals, 1), else_=0)
    loss = case(
        (is_home & (fxs.home_goals < fxs.away_goals), 1),
        (~is_home & (fxs.away_goals < fxs.home_goals), 1),
        else_=0,
    )

    stmt = (
        select(
            func.count().label("matches"),
            func.avg(ts.yellow_cards).label("yc"),
            func.avg(ts.red_cards).label("rc"),
            func.avg(ts.fouls).label("fouls"),
            func.sum(win).label("wins"),
            func.sum(draw).label("draws"),
            func.sum(loss).label("losses"),
        )
        .select_from(
            fxs.__table__.outerjoin(ts.__table__, (ts.fixture_id == fxs.id) & (ts.team_id == team_id))
        )
        .where(
            fxs.referee_id == referee_id,
            fxs.is_finished.is_(True),
            is_team,
        )
    )

    row = (await db.execute(stmt)).one()
    matches = row.matches or 0

    if matches < _MIN_SAMPLES:
        return RefereeTeamHistory(matches=matches, yellow_cards_pg=None, red_cards_pg=None,
                                   fouls_pg=None, wins=row.wins or 0, draws=row.draws or 0,
                                   losses=row.losses or 0)

    return RefereeTeamHistory(
        matches=matches,
        yellow_cards_pg=round(float(row.yc), 2) if row.yc is not None else None,
        red_cards_pg=round(float(row.rc), 2) if row.rc is not None else None,
        fouls_pg=round(float(row.fouls), 2) if row.fouls is not None else None,
        wins=row.wins or 0,
        draws=row.draws or 0,
        losses=row.losses or 0,
    )
