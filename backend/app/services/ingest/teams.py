"""Team upsert. Called whenever we see a team in a fixture payload."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Team


async def upsert_team(session: AsyncSession, team_payload: dict) -> Optional[int]:
    """Idempotent. Returns team_id or None if payload is unusable.

    Updates name/logo on each call — useful when api-sports refreshes branding.
    """
    team_id = team_payload.get("id")
    name = team_payload.get("name")
    if not team_id or not name:
        return None

    stmt = pg_insert(Team).values(
        id=team_id,
        name=name,
        logo_url=team_payload.get("logo"),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[Team.id],
        set_={
            "name": stmt.excluded.name,
            "logo_url": stmt.excluded.logo_url,
        },
    )
    await session.execute(stmt)
    return team_id
