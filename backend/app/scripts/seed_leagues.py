"""Seed the leagues catalog with the curated v1 list.

Run once after `alembic upgrade head`:

    python -m app.scripts.seed_leagues

Idempotent — re-running updates existing rows but doesn't duplicate.

Selection principle (v1, 21 leagues):
- 15 football leagues, Europe + LatAm + US weighted (research-bettor heartland).
- 6 basketball leagues (NBA + Euroleague + 4 more competitive ones).

api-sports football IDs are confirmed from our existing data/leagues.json.
Basketball IDs use api-sports.io's basketball namespace; verify on first
ingest run and adjust here. League IDs are CONFIRMED in code — never trust
ids picked from memory.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.base import async_session_factory
from app.db.models import League, Sport


@dataclass(frozen=True)
class SeedLeague:
    id: int
    name: str
    sport: str          # 'football' | 'basketball'
    country: str
    country_code: str
    is_popular: bool
    sort_order: int
    is_free_tier: bool  # exposed without subscription
    logo_url: str = ""


# --- Sports (catalog) ---
SPORTS = [
    ("football", "Football"),
    ("basketball", "Basketball"),
]


# --- Football v1 leagues (api-sports football IDs) ---
FOOTBALL_LEAGUES: list[SeedLeague] = [
    SeedLeague(39,  "Premier League",        "football", "England",      "GB", True,  1,  True),
    SeedLeague(140, "La Liga",                "football", "Spain",        "ES", True,  2,  True),
    SeedLeague(78,  "Bundesliga",             "football", "Germany",      "DE", True,  3,  True),
    SeedLeague(135, "Serie A",                "football", "Italy",        "IT", True,  4,  True),
    SeedLeague(61,  "Ligue 1",                "football", "France",       "FR", True,  5,  True),
    SeedLeague(203, "Süper Lig",              "football", "Turkey",       "TR", True,  6,  False),
    SeedLeague(2,   "UEFA Champions League",  "football", "World",        "EU", True,  7,  False),
    SeedLeague(3,   "UEFA Europa League",     "football", "World",        "EU", False, 8,  False),
    SeedLeague(88,  "Eredivisie",             "football", "Netherlands",  "NL", False, 9,  False),
    SeedLeague(94,  "Primeira Liga",          "football", "Portugal",     "PT", False, 10, False),
    SeedLeague(71,  "Brasileirão Serie A",    "football", "Brazil",       "BR", True,  11, False),
    SeedLeague(128, "Liga Profesional",       "football", "Argentina",    "AR", False, 12, False),
    SeedLeague(262, "Liga MX",                "football", "Mexico",       "MX", False, 13, False),
    SeedLeague(253, "MLS",                    "football", "USA",          "US", False, 14, False),
    SeedLeague(307, "Saudi Pro League",       "football", "Saudi Arabia", "SA", False, 15, False),
]


# --- Basketball v1 leagues ---
# IMPORTANT: api-sports basketball IDs are NOT the same as football. The values
# below are best-effort. Verify against /leagues on first ingest and correct
# this list before going to prod. Marked TODO so we don't ship guesses.
BASKETBALL_LEAGUES: list[SeedLeague] = [
    SeedLeague(12,  "NBA",              "basketball", "USA",     "US", True,  101, True),   # TODO verify
    SeedLeague(1,   "Euroleague",       "basketball", "Europe",  "EU", True,  102, False),  # TODO verify
    SeedLeague(2,   "EuroCup",          "basketball", "Europe",  "EU", False, 103, False),  # TODO verify
    SeedLeague(27,  "BSL",              "basketball", "Turkey",  "TR", False, 104, False),  # TODO verify
    SeedLeague(11,  "Liga ACB",         "basketball", "Spain",   "ES", False, 105, False),  # TODO verify
    SeedLeague(25,  "Basketball Bundesliga", "basketball", "Germany", "DE", False, 106, False),  # TODO verify
]


async def upsert_sports(session) -> dict[str, int]:
    """Ensure rows exist for each sport; return code → id."""
    result: dict[str, int] = {}
    for code, name in SPORTS:
        existing = (await session.execute(
            select(Sport).where(Sport.code == code)
        )).scalar_one_or_none()
        if existing is None:
            row = Sport(code=code, name=name)
            session.add(row)
            await session.flush()
            result[code] = row.id
        else:
            result[code] = existing.id
    return result


async def upsert_leagues(session, sport_ids: dict[str, int], leagues: list[SeedLeague]) -> int:
    """Upsert leagues. Returns count touched."""
    if not leagues:
        return 0
    rows = [
        {
            "id": l.id,
            "sport_id": sport_ids[l.sport],
            "name": l.name,
            "country": l.country,
            "country_code": l.country_code,
            "logo_url": l.logo_url or None,
            "is_default_popular": l.is_popular,
            "sort_order": l.sort_order,
            "is_active": True,
            "is_free_tier": l.is_free_tier,
        }
        for l in leagues
    ]
    stmt = pg_insert(League).values(rows)
    update_cols = {
        c.name: c
        for c in stmt.excluded
        if c.name not in {"id"}
    }
    stmt = stmt.on_conflict_do_update(index_elements=[League.id], set_=update_cols)
    await session.execute(stmt)
    return len(rows)


async def main() -> None:
    async with async_session_factory() as session:
        sport_ids = await upsert_sports(session)
        n_football = await upsert_leagues(session, sport_ids, FOOTBALL_LEAGUES)
        n_basket = await upsert_leagues(session, sport_ids, BASKETBALL_LEAGUES)
        await session.commit()
        print(f"seeded: {len(sport_ids)} sports, {n_football} football leagues, "
              f"{n_basket} basketball leagues")


if __name__ == "__main__":
    asyncio.run(main())
