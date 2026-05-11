"""GET /v1/teams/{team_id}/squad and team-scoped endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DBSession
from app.db.models import Player, Team, TeamSquad


router = APIRouter(tags=["teams"])


@router.get("/teams/{team_id}")
async def team_detail(team_id: int, db: DBSession):
    team = (await db.execute(select(Team).where(Team.id == team_id))).scalar_one_or_none()
    if team is None:
        return {"team": None}
    return {"team": {
        "id": team.id,
        "name": team.name,
        "short_name": team.short_name,
        "logo": team.logo_url,
        "country": team.country,
        "venue": team.venue,
    }}


@router.get("/teams/{team_id}/squad")
async def team_squad(
    team_id: int,
    db: DBSession,
    league_id: int = Query(..., description="Squad is league-scoped (season ctx)."),
    season: int = Query(...),
):
    stmt = (
        select(Player, TeamSquad.shirt_number, TeamSquad.position)
        .join(TeamSquad, TeamSquad.player_id == Player.id)
        .where(
            TeamSquad.team_id == team_id,
            TeamSquad.league_id == league_id,
            TeamSquad.season_year == season,
            TeamSquad.is_active.is_(True),
        )
        .order_by(TeamSquad.position, Player.name)
    )
    rows = (await db.execute(stmt)).all()
    return {
        "squad": [
            {
                "id": p.id,
                "name": p.name,
                "photo": p.photo_url,
                "nationality": p.nationality,
                "number": number,
                "position": position,
            }
            for p, number, position in rows
        ]
    }
