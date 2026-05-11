"""FastAPI entry point."""
from __future__ import annotations

import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.api.v1 import api_v1_router
from app.core.config import settings


logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENV,
        traces_sample_rate=0.1 if settings.ENV == "prod" else 1.0,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
    )


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs" if settings.ENV != "prod" else None,
    redoc_url=None,
)

# CORS — Flutter mobile app reaches us over HTTPS from the device; web preview
# from claude.ai/code style tools may also hit. Lock down in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV != "prod" else ["https://app.example.com"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get("/healthz")
async def healthz():
    """Liveness probe — must NOT touch DB/Redis. Just confirms the app loop is up."""
    return {"ok": True}


@app.get("/readyz")
async def readyz():
    """Readiness probe — verifies DB connectivity. Used by Fly.io health checks."""
    from sqlalchemy import text
    from app.db.base import async_session_factory
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as e:
        log.error("readyz_db_fail err=%s", e)
        return {"ok": False, "reason": "db_unavailable"}


app.include_router(api_v1_router)
