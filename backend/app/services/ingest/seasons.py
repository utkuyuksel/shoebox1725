"""Season row management — keeps `is_current` exclusive per league."""
from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Season


async def ensure_season(
    session: AsyncSession,
    league_id: int,
    year: int,
    *,
    is_current: bool = False,
    current_round: str | None = None,
) -> int:
    """Idempotently create a (league, year) season row. Returns season.id.

    If `is_current=True`, demotes every other row for the league to false.
    The DB has a partial unique index enforcing this, so we do the demotion
    here BEFORE the upsert to avoid integrity violations.
    """
    if is_current:
        await session.execute(
            update(Season)
            .where(Season.league_id == league_id, Season.is_current.is_(True), Season.year != year)
            .values(is_current=False)
        )

    stmt = pg_insert(Season).values(
        league_id=league_id, year=year,
        is_current=is_current, current_round=current_round,
    )
    update_cols = {"is_current": stmt.excluded.is_current}
    if current_round is not None:
        update_cols["current_round"] = stmt.excluded.current_round
    stmt = stmt.on_conflict_do_update(
        constraint="uniq_seasons_league_year",
        set_=update_cols,
    )
    await session.execute(stmt)

    row = (await session.execute(
        select(Season.id).where(Season.league_id == league_id, Season.year == year)
    )).scalar_one()
    return row
