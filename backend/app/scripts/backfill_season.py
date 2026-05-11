"""Backfill an entire (league, season) from api-sports into Postgres.

Designed for free past-season data — the same code will work for current
season once we buy a paid plan.

Usage:
    # Single league, single season
    python -m app.scripts.backfill_season --league 203 --season 2024

    # Every football league in our seed for one season
    python -m app.scripts.backfill_season --all-football --season 2024

    # Skip stats endpoint (much faster, useful for first pass)
    python -m app.scripts.backfill_season --league 203 --season 2024 --skip-stats

Resumable by design: every step (fixture upsert, stats upsert, aggregate
write) is idempotent. Re-running the same command resumes safely after a
crash — it skips fixture-stats fetches for fixtures whose stats rows
already exist.

Rate-limit aware: respects api-sports.io's per-second cap by sleeping
~0.2s between calls. With the free plan (~10 req/min) you'll want to lower
--concurrency to 1 and bump the per-call sleep manually if needed.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_factory
from app.db.models import (
    Fixture,
    FootballFixtureTeamStats,
    League,
    Sport,
)
from app.integrations.apisports.football import FootballClient
from app.services.ingest.aggregates import (
    recompute_football_team_season_stats_for_league,
    recompute_referee_aggregates_for_league,
    recompute_referee_team_history,
)
from app.services.ingest.fixture_stats import ingest_football_fixture_stats
from app.services.ingest.fixtures import upsert_fixture
from app.services.ingest.seasons import ensure_season
from app.scripts.seed_leagues import FOOTBALL_LEAGUES


log = logging.getLogger(__name__)


async def backfill_league_season(
    client: FootballClient,
    session: AsyncSession,
    league_id: int,
    season_year: int,
    *,
    skip_stats: bool,
    is_current: bool = False,
    max_stats_calls: int | None = None,
    per_call_sleep: float = 0.2,
    dry_run: bool = False,
) -> dict:
    """Backfill one (league, season). Returns simple stats dict.

    `max_stats_calls` caps how many /fixtures/statistics calls we make. Useful
    on the free plan (100/day). Set to e.g. 90 to fit a single league in one
    daily quota cycle. The script is resumable — next run picks up where
    this one stopped.

    `dry_run` skips every api-sports call AND every database write. Useful
    to confirm config + db connectivity before spending quota.
    """
    stats = {
        "fixtures": 0,
        "stats_endpoints_called": 0,
        "fixture_stats_rows": 0,
        "skipped_existing_stats": 0,
        "stats_cap_hit": False,
    }

    if dry_run:
        log.info("DRY_RUN league=%d season=%d — no api-sports calls, no DB writes",
                 league_id, season_year)
        # Still exercise the config path so we catch misconfig early.
        quota_probe = await client.get("status")
        log.info("dry_run_status_probe rate_remaining=%s rate_limit=%s",
                 client.quota_remaining, client.quota_limit)
        return stats

    await ensure_season(session, league_id, season_year, is_current=is_current)
    await session.commit()

    log.info("backfill_start league=%d season=%d", league_id, season_year)
    fixtures_payload = await client.get(
        "fixtures",
        {"league": league_id, "season": season_year, "timezone": "Europe/Istanbul"},
    )
    if not fixtures_payload:
        log.warning("backfill_no_fixtures league=%d season=%d", league_id, season_year)
        return stats

    fixture_ids: list[int] = []
    for fx_payload in fixtures_payload:
        fid = await upsert_fixture(session, fx_payload)
        if fid is not None:
            fixture_ids.append(fid)
            stats["fixtures"] += 1
    await session.commit()
    log.info("backfill_fixtures_done league=%d season=%d fixtures=%d",
             league_id, season_year, stats["fixtures"])

    if not skip_stats:
        already_done = await _fixtures_with_stats(session, fixture_ids)
        pending = [fid for fid in fixture_ids if fid not in already_done]
        stats["skipped_existing_stats"] = len(already_done)
        log.info("backfill_stats_pending league=%d season=%d pending=%d skipped=%d cap=%s",
                 league_id, season_year, len(pending), len(already_done), max_stats_calls)

        for i, fid in enumerate(pending):
            if max_stats_calls is not None and stats["stats_endpoints_called"] >= max_stats_calls:
                stats["stats_cap_hit"] = True
                log.info("backfill_stats_cap_hit league=%d after=%d (resume to continue)",
                         league_id, stats["stats_endpoints_called"])
                break

            stats_payload = await client.fixture_statistics(fid)
            stats["stats_endpoints_called"] += 1
            if stats_payload:
                n = await ingest_football_fixture_stats(session, fid, stats_payload)
                stats["fixture_stats_rows"] += n
            if (i + 1) % 25 == 0:
                await session.commit()
                log.info("backfill_progress league=%d processed=%d/%d",
                         league_id, i + 1, len(pending))
            await asyncio.sleep(per_call_sleep)
        await session.commit()

    # Recompute aggregates for this league/season — fast, all SQL.
    log.info("backfill_aggregate_start league=%d season=%d", league_id, season_year)
    teams_updated = await recompute_football_team_season_stats_for_league(session, league_id, season_year)
    await recompute_referee_aggregates_for_league(session, league_id, season_year)
    await session.commit()
    log.info("backfill_aggregate_done league=%d season=%d teams=%d",
             league_id, season_year, teams_updated)

    return stats


async def _fixtures_with_stats(session: AsyncSession, fixture_ids: Iterable[int]) -> set[int]:
    ids = list(fixture_ids)
    if not ids:
        return set()
    rows = (await session.execute(
        select(FootballFixtureTeamStats.fixture_id).where(
            FootballFixtureTeamStats.fixture_id.in_(ids)
        ).distinct()
    )).scalars().all()
    return set(rows)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--league", type=int, help="api-sports football league id")
    parser.add_argument("--all-football", action="store_true",
                        help="Backfill every football league from the seed list")
    parser.add_argument("--season", type=int, required=True, help="Season start year (e.g. 2024 for 2024-25)")
    parser.add_argument("--skip-stats", action="store_true",
                        help="Skip per-fixture statistics. Faster but no hit-rate/trend data.")
    parser.add_argument("--is-current", action="store_true",
                        help="Mark this season as is_current for each league processed")
    parser.add_argument("--rebuild-ref-history", action="store_true", default=True,
                        help="Rebuild RefereeTeamHistory at the end (default true)")
    parser.add_argument("--max-stats-calls", type=int, default=None,
                        help="Cap fixture-stats API calls per league. Use on the free plan "
                             "(e.g. 90 to fit one league per daily quota). The script is "
                             "resumable — next run picks up the rest.")
    parser.add_argument("--sleep", type=float, default=0.2,
                        help="Sleep between API calls in seconds. Bump to 6+ for free plan "
                             "if you hit the per-minute cap (default 0.2 is Pro-friendly).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip all api-sports calls and DB writes; just probes /status.")
    args = parser.parse_args()

    if not args.league and not args.all_football:
        parser.error("provide --league or --all-football")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    leagues_to_run: list[int] = []
    if args.all_football:
        leagues_to_run = [l.id for l in FOOTBALL_LEAGUES]
    else:
        leagues_to_run = [args.league]

    client = FootballClient()
    try:
        async with async_session_factory() as session:
            total_stats = {"fixtures": 0, "stats_endpoints_called": 0, "fixture_stats_rows": 0}
            for lid in leagues_to_run:
                s = await backfill_league_season(
                    client, session, lid, args.season,
                    skip_stats=args.skip_stats,
                    is_current=args.is_current,
                    max_stats_calls=args.max_stats_calls,
                    per_call_sleep=args.sleep,
                    dry_run=args.dry_run,
                )
                for k in total_stats:
                    total_stats[k] += s.get(k, 0)
                if s.get("stats_cap_hit"):
                    log.info("stats_cap_hit_global stopping further leagues to respect quota")
                    break

            if args.rebuild_ref_history and not args.dry_run:
                log.info("rebuild_ref_history_start")
                n = await recompute_referee_team_history(session)
                await session.commit()
                log.info("rebuild_ref_history_done rows=%d", n)

            log.info("backfill_total %s", total_stats)
            print("DONE:", total_stats)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
