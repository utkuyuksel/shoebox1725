"""Ingest fixtures from api-sports football payloads.

Each fixture payload triggers four side effects:
    1. Upsert both teams (idempotent).
    2. Resolve the referee string → referee_id (or NULL if absent).
    3. Upsert the fixture row.
    4. Return the fixture id for the caller, so the caller can chain
       fixture-stats ingest.

We never raise into the orchestrator for "data was weird" — log and skip.
A failed fixture parse should not poison the whole batch.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Fixture
from app.services.ingest._common import parse_kickoff, safe_int
from app.services.ingest.teams import upsert_team
from app.services.referee.resolver import resolve_referee


log = logging.getLogger(__name__)


async def upsert_fixture(session: AsyncSession, payload: dict) -> Optional[int]:
    """Returns fixture_id on success, None if the payload is unusable."""
    fx = payload.get("fixture") or {}
    league = payload.get("league") or {}
    teams = payload.get("teams") or {}
    goals = payload.get("goals") or {}
    score = payload.get("score") or {}
    halftime = score.get("halftime") or {}

    fixture_id = fx.get("id")
    league_id = league.get("id")
    season_year = league.get("season")
    home = teams.get("home") or {}
    away = teams.get("away") or {}
    kickoff = parse_kickoff(fx.get("date"))
    status = (fx.get("status") or {}).get("short")

    if not (fixture_id and league_id and season_year and home.get("id") and away.get("id") and kickoff and status):
        log.warning("fixture_skip_missing_required fixture_id=%s", fixture_id)
        return None

    # Side-effect 1: teams
    await upsert_team(session, home)
    await upsert_team(session, away)

    # Side-effect 2: referee (string → id). Only finished/in-progress matches
    # carry a real referee value; for NS we leave it null and pick it up on
    # the post-match ingest.
    referee_id = None
    referee_str = fx.get("referee")
    if referee_str:
        referee_id = await resolve_referee(
            session, referee_str, season_year=season_year,
        )

    # Side-effect 3: fixture upsert
    stmt = pg_insert(Fixture).values(
        id=fixture_id,
        league_id=league_id,
        season_year=season_year,
        round=league.get("round"),
        home_team_id=home["id"],
        away_team_id=away["id"],
        kickoff_at=kickoff,
        status=status,
        home_goals=safe_int(goals.get("home")),
        away_goals=safe_int(goals.get("away")),
        home_goals_ht=safe_int(halftime.get("home")),
        away_goals_ht=safe_int(halftime.get("away")),
        referee_id=referee_id,
        venue=(fx.get("venue") or {}).get("name"),
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
    # Don't overwrite a resolved referee_id with NULL on subsequent ingests
    # that come in before the post-match referee string is published.
    if referee_id is not None:
        update_cols["referee_id"] = stmt.excluded.referee_id

    stmt = stmt.on_conflict_do_update(index_elements=[Fixture.id], set_=update_cols)
    await session.execute(stmt)
    return fixture_id
