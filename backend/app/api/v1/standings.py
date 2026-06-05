"""GET /v1/leagues/{league_id}/standings — league table + recent form.

Computed from finished fixtures (see services/standings.py). `season` is
optional; when omitted we use the latest season we have data for.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import DBSession
from app.cache.redis import cache_get_json, cache_set_json, k_standings
from app.services.standings import compute_standings


router = APIRouter(tags=["standings"])

_TTL_STANDINGS = 60 * 30  # 30 min — invalidated naturally as matches finish


@router.get("/leagues/{league_id}/standings")
async def standings(
    league_id: int,
    db: DBSession,
    season: Optional[int] = Query(None, description="defaults to latest loaded season"),
):
    cache_key = k_standings(league_id, season)
    cached = await cache_get_json(cache_key)
    if cached is not None:
        return cached

    payload = await compute_standings(db, league_id, season)
    # Only cache real tables — don't pin an empty result from a transient
    # api-sports failure for the full TTL.
    if payload.get("rows"):
        await cache_set_json(cache_key, payload, ttl_seconds=_TTL_STANDINGS)
    return payload
