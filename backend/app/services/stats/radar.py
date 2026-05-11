"""Radar chart payload: two teams projected onto 8 normalized axes.

Each axis is normalized to the league average so that values cluster around
1.0 — that way the Flutter chart is comparable across leagues, sports, and
metrics. A team with 1.5 on Corners means "50% more than the league avg".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BasketballTeamSeasonStats, FootballTeamSeasonStats


# Stable axis order so the front-end can render without thinking.
FOOTBALL_RADAR_AXES = [
    "goals_for_pg",
    "goals_against_pg",   # inverted: lower is better → handled below
    "shots_total_pg",
    "shots_on_pg",
    "corners_pg",
    "yellow_cards_pg",
    "fouls_pg",
    "xg_pg",
]

# Which axes are "lower is better"? We invert their normalization so the
# team that concedes fewer goals scores higher on the radar.
_INVERTED_AXES = {"goals_against_pg", "yellow_cards_pg", "fouls_pg"}


@dataclass
class RadarPayload:
    axes: list[str]
    home: list[Optional[float]]
    away: list[Optional[float]]


async def football_radar(
    db: AsyncSession,
    home_team_id: int,
    away_team_id: int,
    league_id: int,
    season: int,
) -> RadarPayload:
    Stats = FootballTeamSeasonStats

    rows = (await db.execute(
        select(Stats).where(
            Stats.league_id == league_id,
            Stats.season_year == season,
            Stats.team_id.in_([home_team_id, away_team_id]),
        )
    )).scalars().all()

    by_id = {r.team_id: r for r in rows}

    # League averages per axis — computed from all teams in this season.
    league_avgs: dict[str, Optional[float]] = {}
    for axis in FOOTBALL_RADAR_AXES:
        col = getattr(Stats, axis)
        avg = (await db.execute(
            select(func.avg(col)).where(
                Stats.league_id == league_id,
                Stats.season_year == season,
            )
        )).scalar()
        league_avgs[axis] = float(avg) if avg is not None else None

    def project(team_id: int) -> list[Optional[float]]:
        stats = by_id.get(team_id)
        if stats is None:
            return [None] * len(FOOTBALL_RADAR_AXES)
        out: list[Optional[float]] = []
        for axis in FOOTBALL_RADAR_AXES:
            v = getattr(stats, axis)
            avg = league_avgs.get(axis)
            if v is None or avg is None or avg == 0:
                out.append(None)
                continue
            ratio = float(v) / avg
            if axis in _INVERTED_AXES:
                ratio = 1.0 / ratio if ratio else None
            out.append(round(ratio, 2) if ratio is not None else None)
        return out

    return RadarPayload(
        axes=FOOTBALL_RADAR_AXES,
        home=project(home_team_id),
        away=project(away_team_id),
    )


# --- Basketball ---

BASKETBALL_RADAR_AXES = [
    "points_pg",
    "points_allowed_pg",   # inverted: lower is better
    "fg_pct",
    "three_pct",
    "rebounds_total_pg",
    "assists_pg",
    "steals_pg",
    "turnovers_pg",        # inverted: lower is better
]
_BBALL_INVERTED = {"points_allowed_pg", "turnovers_pg"}


async def basketball_radar(
    db: AsyncSession,
    home_team_id: int,
    away_team_id: int,
    league_id: int,
    season: int,
) -> RadarPayload:
    Stats = BasketballTeamSeasonStats

    rows = (await db.execute(
        select(Stats).where(
            Stats.league_id == league_id,
            Stats.season_year == season,
            Stats.team_id.in_([home_team_id, away_team_id]),
        )
    )).scalars().all()
    by_id = {r.team_id: r for r in rows}

    league_avgs: dict[str, Optional[float]] = {}
    for axis in BASKETBALL_RADAR_AXES:
        col = getattr(Stats, axis)
        avg = (await db.execute(
            select(func.avg(col)).where(
                Stats.league_id == league_id,
                Stats.season_year == season,
            )
        )).scalar()
        league_avgs[axis] = float(avg) if avg is not None else None

    def project(team_id: int) -> list[Optional[float]]:
        stats = by_id.get(team_id)
        if stats is None:
            return [None] * len(BASKETBALL_RADAR_AXES)
        out: list[Optional[float]] = []
        for axis in BASKETBALL_RADAR_AXES:
            v = getattr(stats, axis)
            avg = league_avgs.get(axis)
            if v is None or avg is None or avg == 0:
                out.append(None)
                continue
            ratio = float(v) / avg
            if axis in _BBALL_INVERTED:
                ratio = 1.0 / ratio if ratio else None
            out.append(round(ratio, 2) if ratio is not None else None)
        return out

    return RadarPayload(
        axes=BASKETBALL_RADAR_AXES,
        home=project(home_team_id),
        away=project(away_team_id),
    )
