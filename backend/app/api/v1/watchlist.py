"""Watchlist endpoints. Auth required — only signed-in users have watchlists."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.api.deps import CurrentUser, DBSession
from app.db.models import Fixture, UserWatchlistFixture


router = APIRouter(tags=["watchlist"])


@router.get("/me/watchlist")
async def get_watchlist(user: CurrentUser, db: DBSession):
    stmt = (
        select(Fixture, UserWatchlistFixture.added_at)
        .join(UserWatchlistFixture, UserWatchlistFixture.fixture_id == Fixture.id)
        .where(UserWatchlistFixture.user_id == user.id)
        .order_by(Fixture.kickoff_at.asc())
    )
    rows = (await db.execute(stmt)).all()
    return {
        "fixtures": [
            {"id": fx.id, "kickoff_at": fx.kickoff_at.isoformat(), "status": fx.status,
             "added_at": added_at.isoformat()}
            for fx, added_at in rows
        ]
    }


@router.post("/me/watchlist/{fixture_id}", status_code=204)
async def add_to_watchlist(fixture_id: int, user: CurrentUser, db: DBSession):
    exists = (await db.execute(select(Fixture.id).where(Fixture.id == fixture_id))).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail="fixture not found")
    stmt = pg_insert(UserWatchlistFixture).values(
        user_id=user.id, fixture_id=fixture_id,
    ).on_conflict_do_nothing(index_elements=[UserWatchlistFixture.user_id, UserWatchlistFixture.fixture_id])
    await db.execute(stmt)
    await db.commit()


@router.delete("/me/watchlist/{fixture_id}", status_code=204)
async def remove_from_watchlist(fixture_id: int, user: CurrentUser, db: DBSession):
    await db.execute(
        delete(UserWatchlistFixture).where(
            UserWatchlistFixture.user_id == user.id,
            UserWatchlistFixture.fixture_id == fixture_id,
        )
    )
    await db.commit()
