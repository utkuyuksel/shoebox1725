"""GET /v1/leagues — list leagues grouped by country, with `popular` shortcut."""
from __future__ import annotations

from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DBSession
from app.cache.redis import cache_get_json, cache_set_json, k_leagues
from app.db.models import League, Sport


router = APIRouter(tags=["leagues"])

_TTL_LEAGUES = 60 * 60  # 1 hour — catalog changes rarely


@router.get("/leagues")
async def list_leagues(
    db: DBSession,
    sport: Optional[str] = Query(None, description="football | basketball"),
):
    cache_key = k_leagues(sport or "all")
    cached = await cache_get_json(cache_key)
    if cached is not None:
        return cached

    stmt = (
        select(League, Sport.code)
        .join(Sport, Sport.id == League.sport_id)
        .where(League.is_active.is_(True))
        .order_by(League.country, League.sort_order)
    )
    if sport:
        stmt = stmt.where(Sport.code == sport)

    rows = (await db.execute(stmt)).all()

    leagues_payload = [_serialize(league, sport_code) for league, sport_code in rows]
    popular = [l for l in leagues_payload if l["is_default_popular"]]

    grouped: dict[str, list] = defaultdict(list)
    for l in leagues_payload:
        grouped[l["country"] or "Other"].append(l)

    payload = {
        "count": len(leagues_payload),
        "popular": popular,
        "grouped": dict(grouped),
    }

    await cache_set_json(cache_key, payload, ttl_seconds=_TTL_LEAGUES)
    return payload


def _serialize(league: League, sport_code: str) -> dict:
    return {
        "id": league.id,
        "name": league.name,
        "sport": sport_code,
        "country": league.country,
        "country_code": league.country_code,
        "logo": league.logo_url,
        "is_default_popular": league.is_default_popular,
        "is_free_tier": league.is_free_tier,
        "sort_order": league.sort_order,
    }
