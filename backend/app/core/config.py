"""Centralized settings, sourced from environment via pydantic-settings.

Never hardcode secrets here. All sensitive values come from .env or the
host's secret manager (Fly.io secrets in production).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Identity ---
    PROJECT_NAME: str = "Shoebox API"
    VERSION: str = "0.2.0"
    ENV: Literal["dev", "staging", "prod"] = "dev"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres@localhost:5432/shoebox_db"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- api-sports.io ---
    APISPORTS_KEY: str
    APISPORTS_FOOTBALL_BASE: str = "https://v3.football.api-sports.io"
    APISPORTS_BASKETBALL_BASE: str = "https://v1.basketball.api-sports.io"

    # --- QStash (Upstash) ---
    QSTASH_TOKEN: Optional[str] = None
    QSTASH_SIGNING_KEY: Optional[str] = None         # current key for webhook verification
    QSTASH_NEXT_SIGNING_KEY: Optional[str] = None    # rotation grace
    PUBLIC_BASE_URL: Optional[str] = None            # used to register webhook URLs

    # --- Supabase Auth ---
    SUPABASE_URL: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None        # HS256 secret OR JWKS endpoint base

    # --- RevenueCat ---
    REVENUECAT_WEBHOOK_SECRET: Optional[str] = None

    # --- Observability ---
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- Defaults / scope ---
    DEFAULT_SEASON: int = 2025
    TARGET_LEAGUES_FOOTBALL: int = 25   # cap to keep api-sports Pro plan happy
    TARGET_LEAGUES_BASKETBALL: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
