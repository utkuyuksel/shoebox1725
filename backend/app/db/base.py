"""SQLAlchemy base + async session factory.

Postgres is the canonical store. All app data lives here. Redis is a hot
cache only — losing Redis must never lose data.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# pool_pre_ping=True keeps Neon's serverless connections from going stale.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Single declarative base for every model module."""

    pass


async def get_session() -> AsyncSession:
    """FastAPI dependency for a per-request session."""
    async with async_session_factory() as session:
        yield session
