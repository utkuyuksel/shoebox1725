"""Ingest /fixtures/statistics responses for football.

Payload shape from api-sports:
    [
        {"team": {"id": 645, "name": "Galatasaray"}, "statistics": [...]},
        {"team": {"id": 549, "name": "Fenerbahce"},  "statistics": [...]}
    ]

For each team entry we determine home/away from the fixture row we already
have, flatten the statistics array via FOOTBALL_STAT_TYPE_MAP, and upsert.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Fixture, FootballFixtureTeamStats
from app.services.ingest._common import map_football_stats


log = logging.getLogger(__name__)


async def ingest_football_fixture_stats(
    session: AsyncSession,
    fixture_id: int,
    payload: list[dict],
) -> int:
    """Upsert both teams' per-fixture stats. Returns rows touched."""
    if not payload:
        return 0

    # Need home_team_id to compute is_home for each entry.
    home_id = (await session.execute(
        select(Fixture.home_team_id).where(Fixture.id == fixture_id)
    )).scalar_one_or_none()

    if home_id is None:
        log.warning("ffts_skip_fixture_missing fixture_id=%d", fixture_id)
        return 0

    rows_to_upsert: list[dict] = []
    for team_entry in payload:
        team = team_entry.get("team") or {}
        team_id = team.get("id")
        stats_array = team_entry.get("statistics") or []
        if not team_id:
            continue
        mapped = map_football_stats(stats_array)
        rows_to_upsert.append({
            "fixture_id": fixture_id,
            "team_id": team_id,
            "is_home": team_id == home_id,
            **mapped,
        })

    if not rows_to_upsert:
        return 0

    stmt = pg_insert(FootballFixtureTeamStats).values(rows_to_upsert)
    # On conflict: overwrite all known stat columns. is_home is stable so we
    # don't touch it.
    update_cols = {
        c.name: c for c in stmt.excluded
        if c.name not in {"fixture_id", "team_id", "is_home"}
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=[FootballFixtureTeamStats.fixture_id, FootballFixtureTeamStats.team_id],
        set_=update_cols,
    )
    await session.execute(stmt)
    return len(rows_to_upsert)
