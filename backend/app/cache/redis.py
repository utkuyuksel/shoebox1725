"""Async Redis client + JSON-aware get/set helpers.

Redis is a hot cache only. Anything stored here is recoverable from Postgres
or from api-sports.io. The app must keep working if Redis is empty or down.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings


log = logging.getLogger(__name__)

# Single shared connection pool. asyncio + connection pool = safe to share.
_pool: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    """Lazy singleton. Created on first call; reused thereafter."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
            health_check_interval=30,
        )
    return _pool


async def cache_get_json(key: str) -> Any | None:
    """Read JSON from cache. Returns None on miss or any Redis error.

    A Redis failure must never break the request — the caller will fall back
    to Postgres or the upstream API.
    """
    try:
        raw = await get_redis().get(key)
    except Exception as e:
        log.warning("redis_get_failed key=%s err=%s", key, e)
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("redis_corrupt_json key=%s — deleting", key)
        try:
            await get_redis().delete(key)
        except Exception:
            pass
        return None


async def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    """Write JSON to cache. Silent on Redis errors (cache is opportunistic)."""
    try:
        await get_redis().setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception as e:
        log.warning("redis_set_failed key=%s err=%s", key, e)


async def cache_delete(*keys: str) -> None:
    if not keys:
        return
    try:
        await get_redis().delete(*keys)
    except Exception as e:
        log.warning("redis_delete_failed keys=%s err=%s", keys, e)


# --- Standard key builders. Keep them centralized so we never have key drift. ---

def k_leagues(sport: str) -> str:
    return f"leagues:{sport}"


def k_fixtures(league_id: int, season: int, scope: str = "current_round") -> str:
    return f"fixtures:{league_id}:{season}:{scope}"


def k_match_preview(fixture_id: int) -> str:
    return f"match_preview:{fixture_id}"


def k_team_season_stats(team_id: int, league_id: int, season: int, sport: str) -> str:
    return f"team_season_stats:{sport}:{league_id}:{season}:{team_id}"


def k_team_last_n(team_id: int, n: int) -> str:
    return f"team_last_{n}:{team_id}"


def k_h2h(team_a: int, team_b: int) -> str:
    # Sort so order doesn't matter — same cache hit regardless of perspective.
    lo, hi = sorted([team_a, team_b])
    return f"h2h:{lo}:{hi}"


def k_referee_team_history(referee_id: int, team_id: int) -> str:
    return f"ref_team:{referee_id}:{team_id}"
