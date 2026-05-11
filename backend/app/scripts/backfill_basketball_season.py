"""Backfill an entire (basketball league, season) from api-sports into Postgres.

Mirrors `backfill_season.py` but for basketball. Basketball needs separate
plumbing because:
  - api-sports uses string seasons ("2024-2025") in the basketball namespace
    while we store integer `season_year` (we keep the START year, so 2024).
  - There's no public referee data in basketball, so the football fixture
    upsert path (which resolves a referee string → id) is overkill.
  - The /games endpoint shape differs from football's /fixtures.

Usage:
    # Single league + season
    python -m app.scripts.backfill_basketball_season --league 12 --season 2024

    # Skip per-game stats endpoint (much faster, ~1 API call per league)
    python -m app.scripts.backfill_basketball_season --league 12 --season 2024 --skip-stats

    # All popular basketball leagues (NBA + Euroleague)
    python -m app.scripts.backfill_basketball_season --all-basketball --season 2024

Resumable: per-game stats fetches skip fixtures whose stats rows already exist.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_factory
from app.db.models import (
    BasketballFixtureTeamStats,
    Fixture,
    Team,
)
from app.integrations.apisports.basketball import BasketballClient
from app.services.ingest._common import parse_kickoff, safe_int
from app.services.ingest.aggregates import (
    recompute_basketball_team_season_stats_for_league,
)
from app.services.ingest.seasons import ensure_season
from app.services.ingest.teams import upsert_team


log = logging.getLogger(__name__)


# Popular basketball leagues (matches our DB is_default_popular=true rows).
POPULAR_BASKETBALL_LEAGUES = [12, 120]   # NBA, Euroleague


def season_str(year: int) -> str:
    """Convert integer season start year to api-sports basketball season string.
    2024 → "2024-2025"."""
    return f"{year}-{year + 1}"


async def _upsert_basketball_fixture(session: AsyncSession, payload: dict) -> int | None:
    """Per-game fixture upsert for basketball. Returns fixture_id or None."""
    fixture_id = payload.get("id")
    league = payload.get("league") or {}
    teams = payload.get("teams") or {}
    scores = payload.get("scores") or {}
    home = teams.get("home") or {}
    away = teams.get("away") or {}
    home_scores = scores.get("home") or {}
    away_scores = scores.get("away") or {}

    league_id = league.get("id")
    # api-sports returns season as "2024-2025" string; we store start year.
    season_raw = league.get("season")
    season_year = _parse_season_start(season_raw)
    kickoff = parse_kickoff(payload.get("date"))
    status = (payload.get("status") or {}).get("short")

    if not (fixture_id and league_id and season_year and home.get("id") and away.get("id") and kickoff and status):
        log.warning("basketball_fixture_skip_missing fixture_id=%s", fixture_id)
        return None

    await upsert_team(session, home)
    await upsert_team(session, away)

    # Halftime is the SECOND quarter's running total in basketball (Q1 + Q2).
    home_ht = _ht_total(home_scores)
    away_ht = _ht_total(away_scores)

    stmt = pg_insert(Fixture).values(
        id=fixture_id,
        league_id=league_id,
        season_year=season_year,
        round=league.get("stage") or league.get("week") or league.get("round"),
        home_team_id=home["id"],
        away_team_id=away["id"],
        kickoff_at=kickoff,
        status=status,
        home_goals=safe_int(home_scores.get("total")),
        away_goals=safe_int(away_scores.get("total")),
        home_goals_ht=home_ht,
        away_goals_ht=away_ht,
        referee_id=None,
        venue=(payload.get("venue") or None),
    )
    update_cols = {
        "round":         stmt.excluded.round,
        "status":        stmt.excluded.status,
        "home_goals":    stmt.excluded.home_goals,
        "away_goals":    stmt.excluded.away_goals,
        "home_goals_ht": stmt.excluded.home_goals_ht,
        "away_goals_ht": stmt.excluded.away_goals_ht,
        "kickoff_at":    stmt.excluded.kickoff_at,
        "venue":         stmt.excluded.venue,
    }
    stmt = stmt.on_conflict_do_update(index_elements=[Fixture.id], set_=update_cols)
    await session.execute(stmt)
    return fixture_id


def _parse_season_start(s) -> int | None:
    """Extract the START year. Accepts ints (2024) or 'YYYY-YYYY' strings."""
    if s is None:
        return None
    if isinstance(s, int):
        return s
    s = str(s).strip()
    if s.isdigit():
        return int(s)
    if "-" in s:
        head = s.split("-", 1)[0]
        return int(head) if head.isdigit() else None
    return None


def _ht_total(team_scores: dict) -> int | None:
    """Halftime = Q1 + Q2 total. Some payloads expose `quarter_1`, `quarter_2`."""
    q1 = safe_int(team_scores.get("quarter_1"))
    q2 = safe_int(team_scores.get("quarter_2"))
    if q1 is None and q2 is None:
        return None
    return (q1 or 0) + (q2 or 0)


async def _ingest_game_stats(session: AsyncSession, fixture_id: int,
                              payload: list[dict]) -> int:
    """Map api-sports basketball `games/statistics/teams` response to our
    BasketballFixtureTeamStats rows. Returns rows written."""
    if not payload:
        return 0
    n = 0
    for team_block in payload:
        team = team_block.get("team") or {}
        stats = team_block.get("statistics") or [{}]
        # The endpoint sometimes returns stats as a single dict directly,
        # sometimes as a list with one dict — normalize.
        if isinstance(stats, list):
            stats = stats[0] if stats else {}
        team_id = team.get("id")
        if not team_id:
            continue
        # is_home: we infer from the Fixture row.
        fx = (await session.execute(
            select(Fixture.home_team_id).where(Fixture.id == fixture_id)
        )).scalar_one_or_none()
        is_home = (fx == team_id)

        # Field goal lines come as a "field_goals" sub-object with made/attempts.
        def split(key: str) -> tuple[int | None, int | None]:
            sub = stats.get(key) or {}
            return safe_int(sub.get("total") or sub.get("made")), safe_int(sub.get("attempts"))

        fg_m, fg_a = split("field_goals")
        two_m, two_a = split("twopoint_goals")
        three_m, three_a = split("threepoint_goals")
        ft_m, ft_a = split("freethrows_goals")

        rebounds = stats.get("rebounds") or {}
        stmt = pg_insert(BasketballFixtureTeamStats).values(
            fixture_id=fixture_id,
            team_id=team_id,
            is_home=is_home,
            points=safe_int(stats.get("points")),
            field_goals_made=fg_m,
            field_goals_att=fg_a,
            two_points_made=two_m,
            two_points_att=two_a,
            three_points_made=three_m,
            three_points_att=three_a,
            free_throws_made=ft_m,
            free_throws_att=ft_a,
            rebounds_offensive=safe_int(rebounds.get("offence")),
            rebounds_defensive=safe_int(rebounds.get("defence")),
            assists=safe_int(stats.get("assists")),
            steals=safe_int(stats.get("steals")),
            blocks=safe_int(stats.get("blocks")),
            turnovers=safe_int(stats.get("turnovers")),
            fouls=safe_int(stats.get("personal_fouls") or stats.get("fouls")),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[BasketballFixtureTeamStats.fixture_id,
                            BasketballFixtureTeamStats.team_id],
            set_={
                "points": stmt.excluded.points,
                "field_goals_made": stmt.excluded.field_goals_made,
                "field_goals_att": stmt.excluded.field_goals_att,
                "two_points_made": stmt.excluded.two_points_made,
                "two_points_att": stmt.excluded.two_points_att,
                "three_points_made": stmt.excluded.three_points_made,
                "three_points_att": stmt.excluded.three_points_att,
                "free_throws_made": stmt.excluded.free_throws_made,
                "free_throws_att": stmt.excluded.free_throws_att,
                "rebounds_offensive": stmt.excluded.rebounds_offensive,
                "rebounds_defensive": stmt.excluded.rebounds_defensive,
                "assists": stmt.excluded.assists,
                "steals": stmt.excluded.steals,
                "blocks": stmt.excluded.blocks,
                "turnovers": stmt.excluded.turnovers,
                "fouls": stmt.excluded.fouls,
            },
        )
        await session.execute(stmt)
        n += 1
    return n


async def _fixtures_with_stats(session: AsyncSession, fixture_ids: Iterable[int]) -> set[int]:
    ids = list(fixture_ids)
    if not ids:
        return set()
    rows = (await session.execute(
        select(BasketballFixtureTeamStats.fixture_id).where(
            BasketballFixtureTeamStats.fixture_id.in_(ids)
        ).distinct()
    )).scalars().all()
    return set(rows)


async def backfill_basketball_league_season(
    client: BasketballClient,
    session: AsyncSession,
    league_id: int,
    season_year: int,
    *,
    skip_stats: bool,
    is_current: bool = False,
    max_stats_calls: int | None = None,
    per_call_sleep: float = 0.2,
) -> dict:
    stats = {
        "fixtures": 0,
        "stats_endpoints_called": 0,
        "fixture_stats_rows": 0,
        "skipped_existing_stats": 0,
        "stats_cap_hit": False,
    }

    await ensure_season(session, league_id, season_year, is_current=is_current)
    await session.commit()

    log.info("basketball_backfill_start league=%d season=%d (%s)",
             league_id, season_year, season_str(season_year))
    games_payload = await client.get(
        "games",
        {"league": league_id, "season": season_str(season_year)},
    )
    if not games_payload:
        log.warning("basketball_backfill_no_games league=%d season=%d", league_id, season_year)
        return stats

    fixture_ids: list[int] = []
    for g in games_payload:
        fid = await _upsert_basketball_fixture(session, g)
        if fid is not None:
            fixture_ids.append(fid)
            stats["fixtures"] += 1
    await session.commit()
    log.info("basketball_backfill_fixtures_done league=%d season=%d fixtures=%d",
             league_id, season_year, stats["fixtures"])

    if not skip_stats:
        already_done = await _fixtures_with_stats(session, fixture_ids)
        pending = [fid for fid in fixture_ids if fid not in already_done]
        stats["skipped_existing_stats"] = len(already_done)
        log.info("basketball_stats_pending league=%d pending=%d skipped=%d cap=%s",
                 league_id, len(pending), len(already_done), max_stats_calls)

        for i, fid in enumerate(pending):
            if max_stats_calls is not None and stats["stats_endpoints_called"] >= max_stats_calls:
                stats["stats_cap_hit"] = True
                break

            stats_payload = await client.game_statistics(fid)
            stats["stats_endpoints_called"] += 1
            if stats_payload:
                n = await _ingest_game_stats(session, fid, stats_payload)
                stats["fixture_stats_rows"] += n
            if (i + 1) % 25 == 0:
                await session.commit()
                log.info("basketball_progress league=%d processed=%d/%d",
                         league_id, i + 1, len(pending))
            await asyncio.sleep(per_call_sleep)
        await session.commit()

    log.info("basketball_aggregate_start league=%d season=%d", league_id, season_year)
    teams_updated = await recompute_basketball_team_season_stats_for_league(session, league_id, season_year)
    await session.commit()
    log.info("basketball_aggregate_done league=%d season=%d teams=%d",
             league_id, season_year, teams_updated)

    return stats


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--league", type=int)
    parser.add_argument("--all-basketball", action="store_true")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--skip-stats", action="store_true")
    parser.add_argument("--is-current", action="store_true")
    parser.add_argument("--max-stats-calls", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    if not args.league and not args.all_basketball:
        parser.error("provide --league or --all-basketball")

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    leagues_to_run = POPULAR_BASKETBALL_LEAGUES if args.all_basketball else [args.league]

    client = BasketballClient()
    try:
        async with async_session_factory() as session:
            total = {"fixtures": 0, "stats_endpoints_called": 0, "fixture_stats_rows": 0}
            for lid in leagues_to_run:
                s = await backfill_basketball_league_season(
                    client, session, lid, args.season,
                    skip_stats=args.skip_stats,
                    is_current=args.is_current,
                    max_stats_calls=args.max_stats_calls,
                    per_call_sleep=args.sleep,
                )
                for k in total:
                    total[k] += s.get(k, 0)
                if s.get("stats_cap_hit"):
                    log.info("basketball_stats_cap_hit_global")
                    break
            log.info("basketball_backfill_total %s", total)
            print("DONE:", total)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
