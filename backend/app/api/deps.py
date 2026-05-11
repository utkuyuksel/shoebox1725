"""FastAPI dependencies: DB session, current user (Supabase JWT)."""
from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import async_session_factory


# --- DB session ---

async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db)]


# --- Auth ---

class AuthUser:
    """Minimal user record we extract from a verified Supabase JWT."""

    __slots__ = ("id", "email")

    def __init__(self, id: UUID, email: Optional[str]) -> None:
        self.id = id
        self.email = email


def _decode_jwt(token: str) -> dict:
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET not configured",
        )
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_user(authorization: Annotated[str | None, Header()] = None) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    claims = _decode_jwt(token)
    return AuthUser(id=UUID(claims["sub"]), email=claims.get("email"))


async def maybe_user(authorization: Annotated[str | None, Header()] = None) -> AuthUser | None:
    """For endpoints that adjust behavior based on auth but allow anonymous."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        claims = _decode_jwt(authorization.split(" ", 1)[1])
        return AuthUser(id=UUID(claims["sub"]), email=claims.get("email"))
    except HTTPException:
        return None


CurrentUser = Annotated[AuthUser, Depends(require_user)]
OptionalUser = Annotated[Optional[AuthUser], Depends(maybe_user)]
