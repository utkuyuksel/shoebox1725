"""Referee name → referee_id resolver.

api-sports.io returns the referee as a free-text string on each fixture
(`"Halil Umut Meler, Turkey"`). Hakem-takım eşleşmesi and ref season
aggregates are the whole point of the v1 referee feature, so we have to
turn that string into a stable ID we own.

Resolution order (cheapest → most expensive):

  1. Exact match on `referees.name_normalized`.
  2. Exact match on `referee_aliases.alias_normalized` (manual overrides).
  3. Fuzzy match via pg_trgm similarity ≥ 0.85, single high-confidence row.
  4. Create a new `referees` row.

The fuzzy fallback is conservative on purpose. A wrong merge is harder to
detect later than a duplicate row — duplicates can be merged by adding an
alias and rewriting fixtures.referee_id.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Referee, RefereeAlias


log = logging.getLogger(__name__)

_FUZZY_THRESHOLD = 0.85


def normalize_name(raw: str) -> str:
    """Make a name stable for matching.

    Steps: drop the optional ", Country" suffix, NFKD-decompose to strip
    diacritics, lowercase, replace all non-alphanumeric runs with single
    spaces, then strip. Never raises — returns "" on garbage input.
    """
    if not raw:
        return ""
    # api-sports returns "Name, Country" — drop the country tail.
    name = raw.split(",", 1)[0]
    # NFKD: decompose accents into base + combining marks, then drop marks.
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", " ", name).strip()
    return name


def parse_nationality(raw: str) -> Optional[str]:
    """Pull the country out of `"Name, Country"`. Returns None if absent."""
    if not raw or "," not in raw:
        return None
    return raw.split(",", 1)[1].strip() or None


async def resolve_referee(
    session: AsyncSession,
    raw_name: str,
    *,
    create_if_missing: bool = True,
    season_year: Optional[int] = None,
) -> Optional[int]:
    """Return a referee_id for `raw_name`. Creates a row if missing (default).

    Pass `create_if_missing=False` for read paths that shouldn't write.
    """
    normalized = normalize_name(raw_name)
    if not normalized:
        return None

    # 1. Exact match on referees.
    ref_id = (await session.execute(
        select(Referee.id).where(Referee.name_normalized == normalized)
    )).scalar_one_or_none()
    if ref_id is not None:
        return ref_id

    # 2. Alias table.
    ref_id = (await session.execute(
        select(RefereeAlias.referee_id).where(RefereeAlias.alias_normalized == normalized)
    )).scalar_one_or_none()
    if ref_id is not None:
        return ref_id

    # 3. Fuzzy fallback (pg_trgm). We only accept a *single* row above the
    # threshold — multiple candidates means the auto-merge is unsafe and we
    # fall through to creating a new row, which is the conservative move.
    # Explicit ::text casts are required so asyncpg's prepared-statement type
    # inference doesn't fall back to "unknown" and fail to resolve pg_trgm's
    # similarity() and %% operator.
    # Schema-qualify pg_trgm function/operator: asyncpg's prepared-statement
    # session may have a search_path that excludes public, so an unqualified
    # `similarity()` won't resolve. `OPERATOR(public.%)` does the same for the
    # operator form. Casts keep parameter type inference unambiguous.
    fuzzy_sql = text("""
        SELECT id, public.similarity(name_normalized::text, :q ::text) AS sim
        FROM referees
        WHERE name_normalized::text OPERATOR(public.%) :q ::text
          AND public.similarity(name_normalized::text, :q ::text) >= :threshold ::real
        ORDER BY sim DESC
        LIMIT 2
    """)
    rows = (await session.execute(
        fuzzy_sql, {"q": normalized, "threshold": _FUZZY_THRESHOLD}
    )).all()
    if len(rows) == 1:
        return rows[0].id
    if len(rows) > 1:
        log.info(
            "referee_fuzzy_ambiguous query=%r candidates=%s — creating fresh row",
            normalized,
            [(r.id, float(r.sim)) for r in rows],
        )

    # 4. Create new.
    if not create_if_missing:
        return None
    new_ref = Referee(
        name=raw_name.split(",", 1)[0].strip(),
        name_normalized=normalized,
        nationality=parse_nationality(raw_name),
        first_seen_year=season_year,
    )
    session.add(new_ref)
    await session.flush()  # populate id, but don't commit — caller owns the tx
    log.info("referee_created id=%d name=%r normalized=%r", new_ref.id, new_ref.name, normalized)
    return new_ref.id


async def add_alias(
    session: AsyncSession,
    referee_id: int,
    alias_raw: str,
    note: Optional[str] = None,
) -> None:
    """Manually map an alternate string to an existing referee.

    Idempotent: re-adding the same alias is a no-op.
    """
    alias_norm = normalize_name(alias_raw)
    if not alias_norm:
        return
    exists = (await session.execute(
        select(RefereeAlias.id).where(RefereeAlias.alias_normalized == alias_norm)
    )).scalar_one_or_none()
    if exists is not None:
        return
    session.add(RefereeAlias(
        referee_id=referee_id, alias_normalized=alias_norm, note=note,
    ))
    await session.flush()
