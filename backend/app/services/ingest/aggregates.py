"""Recompute season aggregates from raw fixtures + fixture stats.

Called after a batch of fixtures + stats lands in the DB. Pure SQL — no
in-memory aggregation — because Postgres is way faster than us at this.

Two main entry points:
    - `recompute_football_team_season_stats(...)` for one team
    - `recompute_football_team_season_stats_for_league(...)` for a whole league

A third helper `recompute_referee_aggregates(...)` rebuilds the ref-season
and ref-team-history tables. Cheap enough to run as a single pass after
every backfill.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Iterable

from sqlalchemy import case, delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    BasketballFixtureTeamStats,
    BasketballTeamSeasonStats,
    Fixture,
    FootballFixtureTeamStats,
    FootballTeamSeasonStats,
    RefereeSeasonStats,
    RefereeTeamHistory,
)


log = logging.getLogger(__name__)

_MIN_SAMPLES_HIT_RATE = 3  # below this, hit-rate cells stay NULL


# ----------------------------------------------------------------------------
# Football team season stats
# ----------------------------------------------------------------------------

async def recompute_football_team_season_stats(
    session: AsyncSession,
    team_id: int,
    league_id: int,
    season_year: int,
) -> None:
    """Recompute one team's season stats and upsert."""
    payload = await _compute_football_team_row(session, team_id, league_id, season_year)
    if payload is None:
        return
    stmt = pg_insert(FootballTeamSeasonStats).values(payload)
    update_cols = {c.name: c for c in stmt.excluded if c.name not in {"team_id", "league_id", "season_year"}}
    stmt = stmt.on_conflict_do_update(
        index_elements=[
            FootballTeamSeasonStats.team_id,
            FootballTeamSeasonStats.league_id,
            FootballTeamSeasonStats.season_year,
        ],
        set_=update_cols,
    )
    await session.execute(stmt)


async def recompute_football_team_season_stats_for_league(
    session: AsyncSession,
    league_id: int,
    season_year: int,
) -> int:
    """Recompute aggregates for every team that played in this (league, season)."""
    team_ids = (await session.execute(
        select(Fixture.home_team_id).where(
            Fixture.league_id == league_id, Fixture.season_year == season_year,
        ).union(
            select(Fixture.away_team_id).where(
                Fixture.league_id == league_id, Fixture.season_year == season_year,
            )
        )
    )).scalars().all()
    unique_teams = list(set(team_ids))
    for tid in unique_teams:
        await recompute_football_team_season_stats(session, tid, league_id, season_year)
    return len(unique_teams)


async def _compute_football_team_row(
    session: AsyncSession,
    team_id: int,
    league_id: int,
    season_year: int,
) -> dict | None:
    """Single big query that returns every column we need for one team row.

    We compute *both* per-team perspective (goals_for vs goals_against) and
    overall (corners, cards, fouls — same regardless of perspective) here.
    """
    fxs = Fixture
    ts = FootballFixtureTeamStats

    is_team = (fxs.home_team_id == team_id) | (fxs.away_team_id == team_id)
    is_home = fxs.home_team_id == team_id

    goals_for = case((is_home, fxs.home_goals), else_=fxs.away_goals)
    goals_against = case((is_home, fxs.away_goals), else_=fxs.home_goals)
    total_goals = (fxs.home_goals + fxs.away_goals)
    btts = (fxs.home_goals > 0) & (fxs.away_goals > 0)

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
            func.count().label("played"),
            func.avg(goals_for).label("gf_pg"),
            func.avg(goals_against).label("ga_pg"),
            func.avg(ts.xg).label("xg_pg"),
            func.avg(ts.shots_total).label("shots_total_pg"),
            func.avg(ts.shots_on).label("shots_on_pg"),
            func.avg(ts.corners).label("corners_pg"),
            func.avg(ts.fouls).label("fouls_pg"),
            func.avg(ts.offsides).label("offsides_pg"),
            func.avg(ts.yellow_cards).label("yc_pg"),
            func.avg(ts.red_cards).label("rc_pg"),
            func.avg(ts.saves).label("saves_pg"),
            # Home split
            func.count().filter(is_home).label("home_played"),
            func.avg(goals_for).filter(is_home).label("home_gf_pg"),
            func.avg(goals_against).filter(is_home).label("home_ga_pg"),
            func.avg(ts.corners).filter(is_home).label("home_corners_pg"),
            func.avg(ts.yellow_cards).filter(is_home).label("home_yc_pg"),
            # Away split
            func.count().filter(~is_home).label("away_played"),
            func.avg(goals_for).filter(~is_home).label("away_gf_pg"),
            func.avg(goals_against).filter(~is_home).label("away_ga_pg"),
            func.avg(ts.corners).filter(~is_home).label("away_corners_pg"),
            func.avg(ts.yellow_cards).filter(~is_home).label("away_yc_pg"),
            # Table context
            func.sum(win).label("wins"),
            func.sum(draw).label("draws"),
            func.sum(loss).label("losses"),
            # Hit-rates
            func.avg(case((total_goals > 1.5, 1.0), else_=0.0)).label("o15"),
            func.avg(case((total_goals > 2.5, 1.0), else_=0.0)).label("o25"),
            func.avg(case((total_goals > 3.5, 1.0), else_=0.0)).label("o35"),
            func.avg(case((btts, 1.0), else_=0.0)).label("btts"),
            func.avg(case((ts.corners > 8.5, 1.0), else_=0.0)).label("c85"),
            func.avg(case((ts.corners > 10.5, 1.0), else_=0.0)).label("c105"),
            func.avg(case((ts.yellow_cards + ts.red_cards > 3.5, 1.0), else_=0.0)).label("k35"),
            func.avg(case((ts.yellow_cards + ts.red_cards > 4.5, 1.0), else_=0.0)).label("k45"),
            func.max(fxs.id).label("last_fixture_id"),
        )
        .select_from(
            fxs.__table__.outerjoin(ts.__table__, (ts.fixture_id == fxs.id) & (ts.team_id == team_id))
        )
        .where(
            fxs.league_id == league_id,
            fxs.season_year == season_year,
            fxs.is_finished.is_(True),
            is_team,
        )
    )

    row = (await session.execute(stmt)).one()
    played = row.played or 0
    if played == 0:
        return None

    def hr(v):
        """0..1 → 0..100 percentage, only if we have enough samples."""
        if played < _MIN_SAMPLES_HIT_RATE or v is None:
            return None
        return round(float(v) * 100.0, 2)

    return {
        "team_id": team_id,
        "league_id": league_id,
        "season_year": season_year,
        "played": played,
        "goals_for_pg": _r(row.gf_pg),
        "goals_against_pg": _r(row.ga_pg),
        "xg_pg": _r(row.xg_pg),
        "shots_total_pg": _r(row.shots_total_pg),
        "shots_on_pg": _r(row.shots_on_pg),
        "corners_pg": _r(row.corners_pg),
        "fouls_pg": _r(row.fouls_pg),
        "offsides_pg": _r(row.offsides_pg),
        "yellow_cards_pg": _r(row.yc_pg),
        "red_cards_pg": _r(row.rc_pg),
        "saves_pg": _r(row.saves_pg),
        "home_played": row.home_played or 0,
        "home_goals_for_pg": _r(row.home_gf_pg),
        "home_goals_against_pg": _r(row.home_ga_pg),
        "home_corners_pg": _r(row.home_corners_pg),
        "home_yellow_cards_pg": _r(row.home_yc_pg),
        "away_played": row.away_played or 0,
        "away_goals_for_pg": _r(row.away_gf_pg),
        "away_goals_against_pg": _r(row.away_ga_pg),
        "away_corners_pg": _r(row.away_corners_pg),
        "away_yellow_cards_pg": _r(row.away_yc_pg),
        "wins": row.wins or 0,
        "draws": row.draws or 0,
        "losses": row.losses or 0,
        "over_15_hit_pct": hr(row.o15),
        "over_25_hit_pct": hr(row.o25),
        "over_35_hit_pct": hr(row.o35),
        "btts_hit_pct": hr(row.btts),
        "corners_over_85_pct": hr(row.c85),
        "corners_over_105_pct": hr(row.c105),
        "cards_over_35_pct": hr(row.k35),
        "cards_over_45_pct": hr(row.k45),
        "last_fixture_id": row.last_fixture_id,
    }


def _r(v) -> Decimal | None:
    """Round Numeric outputs to 2dp, return None for nulls."""
    if v is None:
        return None
    return Decimal(str(float(v))).quantize(Decimal("0.01"))


# ----------------------------------------------------------------------------
# Referee aggregates — per-season + per-team
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Basketball team season stats
# ----------------------------------------------------------------------------

async def recompute_basketball_team_season_stats(
    session: AsyncSession,
    team_id: int,
    league_id: int,
    season_year: int,
) -> None:
    payload = await _compute_basketball_team_row(session, team_id, league_id, season_year)
    if payload is None:
        return
    stmt = pg_insert(BasketballTeamSeasonStats).values(payload)
    update_cols = {c.name: c for c in stmt.excluded
                   if c.name not in {"team_id", "league_id", "season_year"}}
    stmt = stmt.on_conflict_do_update(
        index_elements=[
            BasketballTeamSeasonStats.team_id,
            BasketballTeamSeasonStats.league_id,
            BasketballTeamSeasonStats.season_year,
        ],
        set_=update_cols,
    )
    await session.execute(stmt)


async def recompute_basketball_team_season_stats_for_league(
    session: AsyncSession,
    league_id: int,
    season_year: int,
) -> int:
    team_ids = (await session.execute(
        select(Fixture.home_team_id).where(
            Fixture.league_id == league_id, Fixture.season_year == season_year,
        ).union(
            select(Fixture.away_team_id).where(
                Fixture.league_id == league_id, Fixture.season_year == season_year,
            )
        )
    )).scalars().all()
    unique_teams = list(set(team_ids))
    for tid in unique_teams:
        await recompute_basketball_team_season_stats(session, tid, league_id, season_year)
    return len(unique_teams)


async def _compute_basketball_team_row(
    session: AsyncSession,
    team_id: int,
    league_id: int,
    season_year: int,
) -> dict | None:
    fxs = Fixture
    ts = BasketballFixtureTeamStats

    is_team = (fxs.home_team_id == team_id) | (fxs.away_team_id == team_id)
    is_home = fxs.home_team_id == team_id

    # Use BasketballFixtureTeamStats.points for both perspectives; we filter by team_id.
    win = case(
        (is_home & (fxs.home_goals > fxs.away_goals), 1),
        (~is_home & (fxs.away_goals > fxs.home_goals), 1),
        else_=0,
    )
    loss = case(
        (is_home & (fxs.home_goals < fxs.away_goals), 1),
        (~is_home & (fxs.away_goals < fxs.home_goals), 1),
        else_=0,
    )
    points_scored = case((is_home, fxs.home_goals), else_=fxs.away_goals)
    points_allowed = case((is_home, fxs.away_goals), else_=fxs.home_goals)

    stmt = (
        select(
            func.count().label("played"),
            func.avg(points_scored).label("ppg"),
            func.avg(points_allowed).label("ppg_allowed"),
            # FG% etc. averaged from per-fixture stats
            (func.sum(ts.field_goals_made) * 100.0
             / func.nullif(func.sum(ts.field_goals_att), 0)).label("fg_pct"),
            (func.sum(ts.two_points_made) * 100.0
             / func.nullif(func.sum(ts.two_points_att), 0)).label("two_pct"),
            (func.sum(ts.three_points_made) * 100.0
             / func.nullif(func.sum(ts.three_points_att), 0)).label("three_pct"),
            (func.sum(ts.free_throws_made) * 100.0
             / func.nullif(func.sum(ts.free_throws_att), 0)).label("ft_pct"),
            func.avg(ts.two_points_made).label("two_made_pg"),
            func.avg(ts.two_points_att).label("two_att_pg"),
            func.avg(ts.three_points_made).label("three_made_pg"),
            func.avg(ts.three_points_att).label("three_att_pg"),
            func.avg(ts.free_throws_made).label("ft_made_pg"),
            func.avg(ts.free_throws_att).label("ft_att_pg"),
            func.avg(ts.rebounds_offensive).label("reb_off_pg"),
            func.avg(ts.rebounds_defensive).label("reb_def_pg"),
            (func.avg(ts.rebounds_offensive) + func.avg(ts.rebounds_defensive)).label("reb_total_pg"),
            func.avg(ts.assists).label("ast_pg"),
            func.avg(ts.steals).label("stl_pg"),
            func.avg(ts.blocks).label("blk_pg"),
            func.avg(ts.turnovers).label("to_pg"),
            # Home / Away splits
            func.count().filter(is_home).label("home_played"),
            func.avg(points_scored).filter(is_home).label("home_ppg"),
            func.avg(points_allowed).filter(is_home).label("home_ppg_allowed"),
            func.count().filter(~is_home).label("away_played"),
            func.avg(points_scored).filter(~is_home).label("away_ppg"),
            func.avg(points_allowed).filter(~is_home).label("away_ppg_allowed"),
            # W/L
            func.sum(win).label("wins"),
            func.sum(loss).label("losses"),
            func.max(fxs.id).label("last_fixture_id"),
        )
        .select_from(
            fxs.__table__.outerjoin(ts.__table__, (ts.fixture_id == fxs.id) & (ts.team_id == team_id))
        )
        .where(
            fxs.league_id == league_id,
            fxs.season_year == season_year,
            fxs.is_finished.is_(True),
            is_team,
        )
    )

    row = (await session.execute(stmt)).one()
    played = row.played or 0
    if played == 0:
        return None

    return {
        "team_id": team_id,
        "league_id": league_id,
        "season_year": season_year,
        "played": played,
        "points_pg": _r(row.ppg),
        "points_allowed_pg": _r(row.ppg_allowed),
        "fg_pct": _r(row.fg_pct),
        "two_pct": _r(row.two_pct),
        "three_pct": _r(row.three_pct),
        "ft_pct": _r(row.ft_pct),
        "two_made_pg": _r(row.two_made_pg),
        "two_att_pg": _r(row.two_att_pg),
        "three_made_pg": _r(row.three_made_pg),
        "three_att_pg": _r(row.three_att_pg),
        "ft_made_pg": _r(row.ft_made_pg),
        "ft_att_pg": _r(row.ft_att_pg),
        "rebounds_off_pg": _r(row.reb_off_pg),
        "rebounds_def_pg": _r(row.reb_def_pg),
        "rebounds_total_pg": _r(row.reb_total_pg),
        "assists_pg": _r(row.ast_pg),
        "steals_pg": _r(row.stl_pg),
        "blocks_pg": _r(row.blk_pg),
        "turnovers_pg": _r(row.to_pg),
        "home_played": row.home_played or 0,
        "home_points_pg": _r(row.home_ppg),
        "home_points_allowed_pg": _r(row.home_ppg_allowed),
        "away_played": row.away_played or 0,
        "away_points_pg": _r(row.away_ppg),
        "away_points_allowed_pg": _r(row.away_ppg_allowed),
        "wins": row.wins or 0,
        "losses": row.losses or 0,
        "last_fixture_id": row.last_fixture_id,
    }


# ----------------------------------------------------------------------------
# Referee aggregates — per-season + per-team
# ----------------------------------------------------------------------------

async def recompute_referee_aggregates_for_league(
    session: AsyncSession,
    league_id: int,
    season_year: int,
) -> None:
    """Rebuild RefereeSeasonStats for this (league, season).

    We delete + re-insert because the source set is small (~30 refs/league)
    and computing diffs is more code than it's worth.
    """
    fxs = Fixture
    ts = FootballFixtureTeamStats

    # Per-fixture sum of cards/fouls across both teams (so we can later avg
    # per-fixture per-referee). LEFT JOIN ensures fixtures missing stats
    # still get counted toward `matches` but contribute null to averages.
    per_fixture = (
        select(
            fxs.id.label("fid"),
            fxs.referee_id.label("rid"),
            func.coalesce(func.sum(ts.yellow_cards), 0).label("yc"),
            func.coalesce(func.sum(ts.red_cards), 0).label("rc"),
            func.coalesce(func.sum(ts.fouls), 0).label("fouls"),
            case(
                (fxs.home_goals > fxs.away_goals, 1.0),
                else_=0.0,
            ).label("home_win"),
        )
        .select_from(fxs.__table__.outerjoin(ts.__table__, ts.fixture_id == fxs.id))
        .where(
            fxs.league_id == league_id,
            fxs.season_year == season_year,
            fxs.is_finished.is_(True),
            fxs.referee_id.is_not(None),
        )
        .group_by(fxs.id, fxs.referee_id, fxs.home_goals, fxs.away_goals)
        .subquery()
    )

    agg = (
        select(
            per_fixture.c.rid.label("referee_id"),
            func.count().label("matches"),
            func.avg(per_fixture.c.yc).label("yc_pg"),
            func.avg(per_fixture.c.rc).label("rc_pg"),
            func.avg(per_fixture.c.fouls).label("fouls_pg"),
            func.avg(per_fixture.c.home_win).label("home_win_pct"),
        )
        .group_by(per_fixture.c.rid)
    )

    rows = (await session.execute(agg)).all()

    await session.execute(
        delete(RefereeSeasonStats).where(
            RefereeSeasonStats.league_id == league_id,
            RefereeSeasonStats.season_year == season_year,
        )
    )

    if rows:
        await session.execute(
            pg_insert(RefereeSeasonStats),
            [
                {
                    "referee_id": r.referee_id,
                    "league_id": league_id,
                    "season_year": season_year,
                    "matches": r.matches,
                    "yellow_cards_pg": _r(r.yc_pg),
                    "red_cards_pg": _r(r.rc_pg),
                    "fouls_pg": _r(r.fouls_pg),
                    "home_win_pct": _r(Decimal(str(float(r.home_win_pct) * 100.0))) if r.home_win_pct is not None else None,
                }
                for r in rows
            ],
        )


async def recompute_referee_team_history(
    session: AsyncSession,
    referee_ids: Iterable[int] | None = None,
) -> int:
    """Rebuild RefereeTeamHistory rows.

    If `referee_ids` is None, rebuilds for every ref that has at least one
    finished fixture. Cheap — runs in seconds even with thousands of fixtures.
    Returns rows touched.
    """
    fxs = Fixture
    ts = FootballFixtureTeamStats

    # Unpivot fixture into one row per (referee, team) appearance, with
    # win/draw/loss + cards from this team's stats.
    home_view = (
        select(
            fxs.referee_id.label("ref"),
            fxs.home_team_id.label("team"),
            ts.yellow_cards.label("yc"),
            ts.red_cards.label("rc"),
            ts.fouls.label("fouls"),
            case(
                (fxs.home_goals > fxs.away_goals, 1),
                else_=0,
            ).label("win"),
            case((fxs.home_goals == fxs.away_goals, 1), else_=0).label("draw"),
            case(
                (fxs.home_goals < fxs.away_goals, 1),
                else_=0,
            ).label("loss"),
            fxs.id.label("fid"),
        )
        .select_from(fxs.__table__.outerjoin(
            ts.__table__,
            (ts.fixture_id == fxs.id) & (ts.team_id == fxs.home_team_id),
        ))
        .where(fxs.is_finished.is_(True), fxs.referee_id.is_not(None))
    )
    away_view = (
        select(
            fxs.referee_id.label("ref"),
            fxs.away_team_id.label("team"),
            ts.yellow_cards.label("yc"),
            ts.red_cards.label("rc"),
            ts.fouls.label("fouls"),
            case(
                (fxs.away_goals > fxs.home_goals, 1),
                else_=0,
            ).label("win"),
            case((fxs.home_goals == fxs.away_goals, 1), else_=0).label("draw"),
            case(
                (fxs.away_goals < fxs.home_goals, 1),
                else_=0,
            ).label("loss"),
            fxs.id.label("fid"),
        )
        .select_from(fxs.__table__.outerjoin(
            ts.__table__,
            (ts.fixture_id == fxs.id) & (ts.team_id == fxs.away_team_id),
        ))
        .where(fxs.is_finished.is_(True), fxs.referee_id.is_not(None))
    )

    unioned = home_view.union_all(away_view).subquery()

    where_clauses = [True]
    if referee_ids is not None:
        ids = list(referee_ids)
        if not ids:
            return 0
        where_clauses.append(unioned.c.ref.in_(ids))

    agg = (
        select(
            unioned.c.ref.label("referee_id"),
            unioned.c.team.label("team_id"),
            func.count().label("matches"),
            func.avg(unioned.c.yc).label("yc_pg"),
            func.avg(unioned.c.rc).label("rc_pg"),
            func.avg(unioned.c.fouls).label("fouls_pg"),
            func.sum(unioned.c.win).label("wins"),
            func.sum(unioned.c.draw).label("draws"),
            func.sum(unioned.c.loss).label("losses"),
            func.max(unioned.c.fid).label("last_fixture_id"),
        )
        .where(*where_clauses)
        .group_by(unioned.c.ref, unioned.c.team)
    )

    rows = (await session.execute(agg)).all()
    if not rows:
        return 0

    # Wipe rebuilds for the referees we just computed; otherwise stale rows
    # would linger if a team-ref pair drops out of the latest data.
    if referee_ids is None:
        await session.execute(delete(RefereeTeamHistory))
    else:
        await session.execute(
            delete(RefereeTeamHistory).where(RefereeTeamHistory.referee_id.in_(list(referee_ids)))
        )

    await session.execute(
        pg_insert(RefereeTeamHistory),
        [
            {
                "referee_id": r.referee_id,
                "team_id": r.team_id,
                "matches": r.matches,
                "yellow_cards_pg": _r(r.yc_pg),
                "red_cards_pg": _r(r.rc_pg),
                "fouls_pg": _r(r.fouls_pg),
                "wins": r.wins or 0,
                "draws": r.draws or 0,
                "losses": r.losses or 0,
                "last_fixture_id": r.last_fixture_id,
            }
            for r in rows
        ],
    )
    return len(rows)
