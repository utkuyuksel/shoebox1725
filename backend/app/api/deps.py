"""FastAPI dependencies: DB session, current user (Supabase JWT via JWKS).

Supabase migrated from HS256 shared-secret tokens to asymmetric ES256 signing
keys. We verify access tokens against the project's public JWKS endpoint
(cached for an hour) instead of carrying a shared secret. No JWT secret is
stored anywhere; only the project URL.
"""
from __future__ import annotations

import time
from typing import Annotated, Optional
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import async_session_factory


# ─── DB session ────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db)]


# ─── Auth ──────────────────────────────────────────────────────────────

class AuthUser:
    """Minimal user record we extract from a verified Supabase JWT."""
    __slots__ = ("id", "email")

    def __init__(self, id: UUID, email: Optional[str]) -> None:
        self.id = id
        self.email = email


# JWKS is small (<1KB) but we still cache to avoid hitting Supabase on every
# request. TTL is one hour; key rotation is rare and on miss we refresh.
_jwks_cache: Optional[dict] = None
_jwks_cache_until: float = 0.0
_JWKS_TTL_SECONDS = 3600


def _jwks_url() -> str:
    if not settings.SUPABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL not configured",
        )
    return f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"


async def _fetch_jwks(force: bool = False) -> dict:
    global _jwks_cache, _jwks_cache_until
    now = time.time()
    if not force and _jwks_cache is not None and now < _jwks_cache_until:
        return _jwks_cache

    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(_jwks_url())
        r.raise_for_status()
    _jwks_cache = r.json()
    _jwks_cache_until = now + _JWKS_TTL_SECONDS
    return _jwks_cache


def _key_for_kid(jwks: dict, kid: str):
    """Look up the public key for the given Key ID and convert to a PEM/EC key
    via PyJWK. Returns None if the kid is unknown."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.PyJWK(key).key
    return None


async def _decode_supabase_jwt(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Malformed token: {e}")

    kid = header.get("kid")
    alg = header.get("alg") or "ES256"
    if not kid:
        raise HTTPException(status_code=401, detail="Token missing 'kid' header")

    jwks = await _fetch_jwks()
    key = _key_for_kid(jwks, kid)
    if key is None:
        # Possible key rotation — force one refresh and retry once.
        jwks = await _fetch_jwks(force=True)
        key = _key_for_kid(jwks, kid)
        if key is None:
            raise HTTPException(status_code=401, detail=f"Unknown signing key: {kid}")

    try:
        return jwt.decode(
            token,
            key,
            algorithms=[alg],
            # Supabase issues tokens with `aud="authenticated"`. We don't
            # enforce it here because the validation is environment-specific
            # and we already trust the issuer key.
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def require_user(authorization: Annotated[str | None, Header()] = None) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    claims = await _decode_supabase_jwt(token)
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim")
    return AuthUser(id=UUID(sub), email=claims.get("email"))


async def maybe_user(authorization: Annotated[str | None, Header()] = None) -> AuthUser | None:
    """For endpoints that adjust behaviour by auth state but allow anonymous."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        claims = await _decode_supabase_jwt(authorization.split(" ", 1)[1])
        sub = claims.get("sub")
        if not sub:
            return None
        return AuthUser(id=UUID(sub), email=claims.get("email"))
    except HTTPException:
        return None


CurrentUser = Annotated[AuthUser, Depends(require_user)]
OptionalUser = Annotated[Optional[AuthUser], Depends(maybe_user)]
