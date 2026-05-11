"""GET /v1/match/{fixture_id} — the meat of the app.

Single endpoint that returns everything the match preview screen needs:
  - basic fixture info
  - both teams' season averages
  - home/away splits
  - hit-rates (Over/Under, BTTS, Corners, Cards)
  - radar-chart payload (8 dimensions, normalized to league average)
  - trend graph payload (last 10 matches for both teams)
  - H2H summary (last 10)
  - referee context (if assigned): season averages + per-team history
  - rule-based insight cards

Computation lives in app/services/* — this file just orchestrates and shapes
the response.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, OptionalUser
from app.cache.redis import cache_get_json, cache_set_json, k_match_preview
from app.db.models import Fixture
from app.services.match_preview import build_match_preview


router = APIRouter(tags=["match"])

_TTL_PREVIEW = 60 * 30  # 30 min, invalidated by worker when a match in round finishes


@router.get("/match/{fixture_id}")
async def match_preview(fixture_id: int, db: DBSession, user: OptionalUser):
    cache_key = k_match_preview(fixture_id)
    cached = await cache_get_json(cache_key)
    if cached is not None:
        # Premium filtering happens at serialization time so cache is shared.
        return _apply_premium_filter(cached, user)

    fx = (await db.execute(
        select(Fixture).where(Fixture.id == fixture_id)
    )).scalar_one_or_none()

    if fx is None:
        raise HTTPException(status_code=404, detail="fixture not found")

    preview = await build_match_preview(db, fx)

    await cache_set_json(cache_key, preview, ttl_seconds=_TTL_PREVIEW)
    return _apply_premium_filter(preview, user)


def _apply_premium_filter(preview: dict, user) -> dict:
    """Free tier sees the basics; premium sees hit-rate, splits, ref history, insights.

    In dev/staging we serve everything so the UI is reviewable without auth.
    Paywall enforcement is re-enabled when ENV=prod.
    """
    from app.core.config import settings
    if settings.ENV != "prod":
        return preview
    is_premium = bool(user and getattr(user, "is_premium", False))
    if is_premium:
        return preview

    # Shallow copy + mask premium sections (front-end will show paywall CTA).
    out = dict(preview)
    if "hit_rates" in out:
        out["hit_rates_locked"] = True
        out["hit_rates"] = None
    if "splits" in out:
        out["splits_locked"] = True
        out["splits"] = None
    if "referee_team_history" in out:
        out["referee_team_history_locked"] = True
        out["referee_team_history"] = None
    if "insights" in out and out["insights"]:
        # show 1 insight, lock the rest
        out["insights_total"] = len(out["insights"])
        out["insights"] = out["insights"][:1]
        out["insights_locked"] = out["insights_total"] > 1
    return out
