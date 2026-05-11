"""Hit-rate calculator.

For a given team's finished fixtures in the current season, compute the
percentage of matches that hit common betting thresholds. Pure SQL — fast.

We compute it from `fixtures` (canonical) rather than from precomputed
season totals, because hit-rate is about *individual fixture outcomes*, not
averages. Cached results are stored in football_team_season_stats by the
worker so the API can serve them in a single read.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Fixture, FootballFixtureTeamStats


@dataclass
class FootballHitRates:
    """All percentages are 0-100. None means "not enough matches" (<3)."""
    matches: int
    over_15_pct: Optional[float]
    over_25_pct: Optional[float]
    over_35_pct: Optional[float]
    btts_pct: Optional[float]
    corners_over_85_pct: Optional[float]
    corners_over_105_pct: Optional[float]
    cards_over_35_pct: Optional[float]
    cards_over_45_pct: Optional[float]


_MIN_SAMPLES = 3


async def compute_football_hit_rates(
    db: AsyncSession,
    team_id: int,
    league_id: int,
    season: int,
    home_only: bool = False,
    away_only: bool = False,
) -> FootballHitRates:
    """Compute hit-rates for a team's finished matches in (league, season).

    `home_only` / `away_only` filter to splits (mutually exclusive).
    """
    if home_only and away_only:
        raise ValueError("home_only and away_only are mutually exclusive")

    # Subselect: for each finished fixture this team played, get total goals
    # and the team's per-match cards/corners from the fixture stats join.
    fxs = Fixture
    ts = FootballFixtureTeamStats

    is_team = (fxs.home_team_id == team_id) | (fxs.away_team_id == team_id)
    is_home = fxs.home_team_id == team_id

    where_clauses = [
        fxs.league_id == league_id,
        fxs.season_year == season,
        fxs.is_finished.is_(True),
        is_team,
    ]
    if home_only:
        where_clauses.append(is_home)
    if away_only:
        where_clauses.append(~is_home)

    total_goals = (fxs.home_goals + fxs.away_goals)
    btts = (fxs.home_goals > 0) & (fxs.away_goals > 0)

    stmt = (
        select(
            func.count().label("matches"),
            func.sum(case((total_goals > 1.5, 1), else_=0)).label("o15"),
            func.sum(case((total_goals > 2.5, 1), else_=0)).label("o25"),
            func.sum(case((total_goals > 3.5, 1), else_=0)).label("o35"),
            func.sum(case((btts, 1), else_=0)).label("btts"),
            func.sum(case((ts.corners > 8.5, 1), else_=0)).label("corners_85"),
            func.sum(case((ts.corners > 10.5, 1), else_=0)).label("corners_105"),
            func.sum(case((ts.yellow_cards + ts.red_cards > 3.5, 1), else_=0)).label("cards_35"),
            func.sum(case((ts.yellow_cards + ts.red_cards > 4.5, 1), else_=0)).label("cards_45"),
        )
        .select_from(
            fxs.__table__.outerjoin(ts.__table__, (ts.fixture_id == fxs.id) & (ts.team_id == team_id))
        )
        .where(*where_clauses)
    )

    row = (await db.execute(stmt)).one()
    matches = row.matches or 0

    def pct(numer) -> Optional[float]:
        if matches < _MIN_SAMPLES or numer is None:
            return None
        return round(100.0 * float(numer) / matches, 1)

    return FootballHitRates(
        matches=matches,
        over_15_pct=pct(row.o15),
        over_25_pct=pct(row.o25),
        over_35_pct=pct(row.o35),
        btts_pct=pct(row.btts),
        corners_over_85_pct=pct(row.corners_85),
        corners_over_105_pct=pct(row.corners_105),
        cards_over_35_pct=pct(row.cards_35),
        cards_over_45_pct=pct(row.cards_45),
    )
