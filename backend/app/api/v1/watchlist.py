"""Watchlist endpoints. Auth required — only signed-in users have watchlists.

The list response is enriched with league + team names + score so the mobile
client can render the list without fanning out to other endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import aliased

from app.api.deps import CurrentUser, DBSession
from app.db.models import Fixture, League, Team, User, UserWatchlistFixture


router = APIRouter(tags=["watchlist"])


async def _ensure_user_mirror(db: DBSession, user_id, email):
    """Lazily upsert the user mirror row. Watchlist FK requires the user row
    to exist, but Supabase Auth is the source of truth so we don't pre-create
    on sign-up."""
    stmt = (
        pg_insert(User)
        .values(id=user_id, email=email)
        .on_conflict_do_nothing(index_elements=[User.id])
    )
    await db.execute(stmt)


@router.get("/me/watchlist")
async def get_watchlist(user: CurrentUser, db: DBSession):
    home = aliased(Team)
    away = aliased(Team)
    stmt = (
        select(
            Fixture,
            League.name,
            League.logo_url,
            League.country_code,
            home.name,
            home.logo_url,
            away.name,
            away.logo_url,
            UserWatchlistFixture.added_at,
        )
        .join(UserWatchlistFixture, UserWatchlistFixture.fixture_id == Fixture.id)
        .join(League, League.id == Fixture.league_id)
        .join(home, home.id == Fixture.home_team_id)
        .join(away, away.id == Fixture.away_team_id)
        .where(UserWatchlistFixture.user_id == user.id)
        .order_by(Fixture.kickoff_at.asc())
    )
    rows = (await db.execute(stmt)).all()
    return {
        "count": len(rows),
        "fixtures": [
            {
                "id": fx.id,
                "league_id": fx.league_id,
                "league_name": lname,
                "league_logo": llogo,
                "league_country_code": lcc,
                "kickoff_at": fx.kickoff_at.isoformat(),
                "status": fx.status,
                "home_team_id": fx.home_team_id,
                "home_team_name": hname,
                "home_team_logo": hlogo,
                "away_team_id": fx.away_team_id,
                "away_team_name": aname,
                "away_team_logo": alogo,
                "home_goals": fx.home_goals,
                "away_goals": fx.away_goals,
                "added_at": added_at.isoformat(),
            }
            for fx, lname, llogo, lcc, hname, hlogo, aname, alogo, added_at in rows
        ],
    }


@router.post("/me/watchlist/{fixture_id}", status_code=204)
async def add_to_watchlist(fixture_id: int, user: CurrentUser, db: DBSession):
    exists = (await db.execute(select(Fixture.id).where(Fixture.id == fixture_id))).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail="fixture not found")
    await _ensure_user_mirror(db, user.id, user.email)
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
