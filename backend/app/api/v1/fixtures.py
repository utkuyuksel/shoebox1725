"""GET /v1/leagues/{league_id}/fixtures — current round + status-aware fixture list."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.api.deps import DBSession
from app.cache.redis import cache_get_json, cache_set_json, k_fixtures
from app.db.models import Fixture, Season, Team


router = APIRouter(tags=["fixtures"])

_TTL_FIXTURES = 60 * 15  # 15 min — refresh aggressively as kickoff approaches


@router.get("/leagues/{league_id}/fixtures")
async def league_fixtures(league_id: int, db: DBSession):
    # current season for the league
    season = (await db.execute(
        select(Season).where(Season.league_id == league_id, Season.is_current.is_(True))
    )).scalar_one_or_none()
    if season is None:
        return {"league_id": league_id, "matches": []}

    cache_key = k_fixtures(league_id, season.year, scope=season.current_round or "current")
    cached = await cache_get_json(cache_key)
    if cached is not None:
        return cached

    # Pull this round's fixtures + both team entities in one query via ORM aliases.
    HomeTeam = aliased(Team)
    AwayTeam = aliased(Team)
    stmt = (
        select(Fixture, HomeTeam, AwayTeam)
        .join(HomeTeam, HomeTeam.id == Fixture.home_team_id)
        .join(AwayTeam, AwayTeam.id == Fixture.away_team_id)
        .where(
            Fixture.league_id == league_id,
            Fixture.season_year == season.year,
            Fixture.round == season.current_round,
        )
        .order_by(Fixture.kickoff_at.asc())
    )
    rows = (await db.execute(stmt)).all()

    matches = [
        {
            "id": fx.id,
            "kickoff_at": fx.kickoff_at.isoformat(),
            "status": fx.status,
            "round": fx.round,
            "home": {
                "id": h.id, "name": h.name, "logo": h.logo_url,
                "goals": fx.home_goals,
            },
            "away": {
                "id": a.id, "name": a.name, "logo": a.logo_url,
                "goals": fx.away_goals,
            },
        }
        for fx, h, a in rows
    ]

    payload = {"league_id": league_id, "season": season.year, "round": season.current_round, "matches": matches}
    await cache_set_json(cache_key, payload, ttl_seconds=_TTL_FIXTURES)
    return payload
