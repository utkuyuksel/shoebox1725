"""GET /v1/leagues/{league_id}/fixtures — sport-aware fixture list.

Football leagues run in rounds (e.g. "Regular Season - 28"), so we filter
the response to the current round only. Basketball leagues like the NBA
don't have a meaningful round/week concept — games are continuous, so we
return a recency-anchored slice (last N played + next N scheduled).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.api.deps import DBSession
from app.cache.redis import cache_get_json, cache_set_json, k_fixtures
from app.db.models import Fixture, League, Season, Sport, Team


router = APIRouter(tags=["fixtures"])

_TTL_FIXTURES = 60 * 15           # 15 min — refresh aggressively as kickoff approaches
_BASKETBALL_RECENT = 12           # Last N finished games to surface
_BASKETBALL_UPCOMING = 20         # Next N scheduled games to surface


@router.get("/leagues/{league_id}/fixtures")
async def league_fixtures(league_id: int, db: DBSession):
    # current season for the league
    season = (await db.execute(
        select(Season).where(Season.league_id == league_id, Season.is_current.is_(True))
    )).scalar_one_or_none()
    if season is None:
        return {"league_id": league_id, "matches": []}

    # Sport code drives the filter strategy. Football → round filter,
    # basketball → date window. Anything else falls back to round.
    sport_code = (await db.execute(
        select(Sport.code).join(League, League.sport_id == Sport.id).where(League.id == league_id)
    )).scalar_one_or_none()

    cache_key = k_fixtures(
        league_id, season.year,
        scope=season.current_round or sport_code or "current",
    )
    cached = await cache_get_json(cache_key)
    if cached is not None:
        return cached

    HomeTeam = aliased(Team)
    AwayTeam = aliased(Team)
    stmt = (
        select(Fixture, HomeTeam, AwayTeam)
        .join(HomeTeam, HomeTeam.id == Fixture.home_team_id)
        .join(AwayTeam, AwayTeam.id == Fixture.away_team_id)
        .where(
            Fixture.league_id == league_id,
            Fixture.season_year == season.year,
        )
        .order_by(Fixture.kickoff_at.asc())
    )

    if sport_code == "basketball":
        # Strategy: take the N most-recent finished games (DESC) and the
        # next N scheduled games (ASC), then union + re-sort. This works
        # in-season, mid-week, and during the off-season without a single
        # "anchor date" heuristic to get wrong.
        now = datetime.now(timezone.utc)

        finished_stmt = (
            select(Fixture, HomeTeam, AwayTeam)
            .join(HomeTeam, HomeTeam.id == Fixture.home_team_id)
            .join(AwayTeam, AwayTeam.id == Fixture.away_team_id)
            .where(
                Fixture.league_id == league_id,
                Fixture.season_year == season.year,
                Fixture.kickoff_at <= now,
            )
            .order_by(Fixture.kickoff_at.desc())
            .limit(_BASKETBALL_RECENT)
        )
        upcoming_stmt = (
            select(Fixture, HomeTeam, AwayTeam)
            .join(HomeTeam, HomeTeam.id == Fixture.home_team_id)
            .join(AwayTeam, AwayTeam.id == Fixture.away_team_id)
            .where(
                Fixture.league_id == league_id,
                Fixture.season_year == season.year,
                Fixture.kickoff_at > now,
            )
            .order_by(Fixture.kickoff_at.asc())
            .limit(_BASKETBALL_UPCOMING)
        )

        finished = (await db.execute(finished_stmt)).all()
        upcoming = (await db.execute(upcoming_stmt)).all()
        # Merge and sort ascending by kickoff so the UI shows oldest-first.
        rows = sorted(list(finished) + list(upcoming), key=lambda r: r[0].kickoff_at)
    else:
        # Football: filter to the current round when it's set.
        if season.current_round:
            stmt = stmt.where(Fixture.round == season.current_round)
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

    payload = {
        "league_id": league_id,
        "season": season.year,
        "round": season.current_round,
        "sport": sport_code,
        "matches": matches,
    }
    await cache_set_json(cache_key, payload, ttl_seconds=_TTL_FIXTURES)
    return payload
