"""Async base client for api-sports.io.

- Single shared httpx.AsyncClient per sport (connection pooling).
- Exponential backoff for 429 + 5xx.
- Surfaces the daily quota headers so we can shed load before exhausting them.
- Never raises into the caller for upstream failures; returns None and lets
  the caller decide whether to fall back to cached / DB data.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import httpx

from app.core.config import settings


log = logging.getLogger(__name__)


class APISportsError(Exception):
    """Raised only for programmer errors (invalid config). Upstream errors
    return None from get()."""


class APISportsClient:
    """One client per sport. Reuse instances — they hold a connection pool."""

    base_url: str

    def __init__(self, base_url: str, sport_label: str):
        if not settings.APISPORTS_KEY:
            raise APISportsError("APISPORTS_KEY env var is required")

        self.base_url = base_url.rstrip("/")
        self.sport_label = sport_label

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"x-apisports-key": settings.APISPORTS_KEY},
            timeout=httpx.Timeout(20.0, connect=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

        # Latest known quota state from response headers. Best-effort.
        self.quota_remaining: Optional[int] = None
        self.quota_limit: Optional[int] = None

    async def close(self) -> None:
        await self._client.aclose()

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Optional[list[dict]]:
        """GET /{endpoint}, returns the `response` array on success, None otherwise."""
        max_attempts = 4
        backoff = 1.0

        for attempt in range(1, max_attempts + 1):
            try:
                r = await self._client.get(endpoint, params=params)
            except httpx.HTTPError as e:
                log.warning("apisports_network sport=%s endpoint=%s attempt=%d err=%s",
                            self.sport_label, endpoint, attempt, e)
                if attempt == max_attempts:
                    return None
                await asyncio.sleep(backoff)
                backoff *= 2
                continue

            self._capture_quota_headers(r)

            if r.status_code == 200:
                payload = r.json()
                # api-sports puts errors in the body even on 200. Surface them.
                errors = payload.get("errors")
                if errors:
                    log.warning("apisports_body_error sport=%s endpoint=%s errors=%s",
                                self.sport_label, endpoint, errors)
                    # Some "errors" are just rate-limit warnings — still return the response.
                    if isinstance(errors, dict) and any("rate" in str(v).lower() for v in errors.values()):
                        return None
                return payload.get("response") or []

            if r.status_code in (429, 500, 502, 503, 504):
                log.warning("apisports_retryable sport=%s endpoint=%s status=%d attempt=%d",
                            self.sport_label, endpoint, r.status_code, attempt)
                if attempt == max_attempts:
                    return None
                await asyncio.sleep(backoff)
                backoff *= 2
                continue

            # 4xx other than 429 are programming/config errors; don't retry.
            log.error("apisports_client_error sport=%s endpoint=%s status=%d body=%s",
                      self.sport_label, endpoint, r.status_code, r.text[:300])
            return None

        return None

    def _capture_quota_headers(self, r: httpx.Response) -> None:
        try:
            rem = r.headers.get("x-ratelimit-requests-remaining")
            lim = r.headers.get("x-ratelimit-requests-limit")
            if rem is not None:
                self.quota_remaining = int(rem)
            if lim is not None:
                self.quota_limit = int(lim)
        except (ValueError, TypeError):
            pass
