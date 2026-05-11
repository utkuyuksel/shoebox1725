"""Seed synthetic squads + per-player season stats so the squad/player
detail screens have something to render in dev.

Adds:
  - ~12 players for Smoke FC (id 9_900_001) and Test United (9_900_002)
  - Squad rows linking players → team for league 203, season 2024
  - football_player_season_stats with position-aware realistic ranges

Idempotent — re-running upserts.

Run:
    python -m app.scripts.add_squad_data
"""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.base import async_session_factory
from app.db.models import (
    FootballPlayerSeasonStats,
    Player,
    Team,
    TeamSquad,
)


LEAGUE_ID = 203
SEASON_YEAR = 2024
HOME_TEAM = 9_900_001       # Smoke FC
AWAY_TEAM = 9_900_002       # Test United


@dataclass(frozen=True)
class SeedPlayer:
    id: int
    name: str
    nationality: str
    position: str            # 'G' | 'D' | 'M' | 'F'
    shirt: int
    height_cm: int


SMOKE_FC_SQUAD: list[SeedPlayer] = [
    SeedPlayer(10001, "Mehmet Goalie",    "Turkey",     "G", 1,  192),
    SeedPlayer(10002, "John Defender",    "England",    "D", 4,  186),
    SeedPlayer(10003, "Erik Stopper",     "Sweden",     "D", 5,  189),
    SeedPlayer(10004, "Diego Wing",       "Argentina",  "D", 12, 178),
    SeedPlayer(10005, "Marcus Holder",    "Brazil",     "D", 3,  180),
    SeedPlayer(10006, "Luka Playmaker",   "Croatia",    "M", 10, 175),
    SeedPlayer(10007, "Andrea Engine",    "Italy",      "M", 8,  181),
    SeedPlayer(10008, "Pablo Roamer",     "Spain",      "M", 6,  179),
    SeedPlayer(10009, "Kevin Striker",    "Belgium",    "F", 9,  184),
    SeedPlayer(10010, "Mo Winger",        "Egypt",      "F", 7,  175),
    SeedPlayer(10011, "Bruno Forward",    "Portugal",   "F", 11, 173),
]

TEST_UNITED_SQUAD: list[SeedPlayer] = [
    SeedPlayer(10012, "Manuel Gloves",    "Germany",    "G", 1,  193),
    SeedPlayer(10013, "Sergio Stopper",   "Spain",      "D", 4,  184),
    SeedPlayer(10014, "Trent Wing",       "England",    "D", 66, 175),
    SeedPlayer(10015, "Theo Lateral",     "France",     "D", 19, 180),
    SeedPlayer(10016, "Niko Mind",        "Brazil",     "M", 10, 177),
    SeedPlayer(10017, "Kevin Box",        "Belgium",    "M", 17, 181),
    SeedPlayer(10018, "Pedri Spark",      "Spain",      "M", 8,  174),
    SeedPlayer(10019, "Erling Hammer",    "Norway",     "F", 9,  194),
    SeedPlayer(10020, "Vinicius Flash",   "Brazil",     "F", 7,  176),
    SeedPlayer(10021, "Harry Tap",        "England",    "F", 10, 188),
]


def _stats_for(position: str) -> dict:
    """Position-aware realistic per-game ranges."""
    g = random.gauss
    appearances = max(3, int(g(15, 5)))
    started = max(0, appearances - random.randint(0, 4))
    minutes_pg = round(g(78, 10), 1) if started > 5 else round(g(35, 12), 1)
    rating = round(max(5.8, min(8.2, g(7.0, 0.35))), 2)

    if position == "G":
        return {
            "appearances": appearances, "started": started,
            "minutes_pg": minutes_pg, "rating": rating,
            "goals": 0, "assists": 0,
            "shots_pg": 0.0, "shots_on_pg": 0.0,
            "passes_pg": round(g(28, 6), 1),
            "passes_accurate_pg": round(g(22, 5), 1),
            "pass_accuracy_pct": round(max(60, min(90, g(78, 5))), 1),
            "tackles_pg": 0.0,
            "interceptions_pg": round(g(0.3, 0.2), 2),
            "fouls_pg": round(g(0.2, 0.1), 2),
            "was_fouled_pg": round(g(0.1, 0.1), 2) if False else 0.0,
            "yellow_cards_pg": round(g(0.05, 0.05), 3),
            "red_cards_pg": 0.0,
        }
    if position == "D":
        return {
            "appearances": appearances, "started": started,
            "minutes_pg": minutes_pg, "rating": rating,
            "goals": random.randint(0, 3),
            "assists": random.randint(0, 4),
            "shots_pg": round(max(0, g(0.7, 0.3)), 2),
            "shots_on_pg": round(max(0, g(0.25, 0.15)), 2),
            "passes_pg": round(g(55, 10), 1),
            "passes_accurate_pg": round(g(46, 8), 1),
            "pass_accuracy_pct": round(max(70, min(92, g(83, 4))), 1),
            "tackles_pg": round(max(0, g(2.4, 0.6)), 2),
            "interceptions_pg": round(max(0, g(1.6, 0.5)), 2),
            "fouls_pg": round(max(0, g(1.3, 0.4)), 2),
            "was_fouled_pg": 0.0,
            "yellow_cards_pg": round(max(0, g(0.22, 0.1)), 3),
            "red_cards_pg": round(max(0, g(0.02, 0.02)), 3),
        }
    if position == "M":
        return {
            "appearances": appearances, "started": started,
            "minutes_pg": minutes_pg, "rating": rating,
            "goals": random.randint(1, 8),
            "assists": random.randint(2, 9),
            "shots_pg": round(max(0, g(1.6, 0.6)), 2),
            "shots_on_pg": round(max(0, g(0.65, 0.3)), 2),
            "passes_pg": round(g(70, 15), 1),
            "passes_accurate_pg": round(g(60, 12), 1),
            "pass_accuracy_pct": round(max(75, min(94, g(86, 4))), 1),
            "tackles_pg": round(max(0, g(1.8, 0.5)), 2),
            "interceptions_pg": round(max(0, g(1.3, 0.4)), 2),
            "fouls_pg": round(max(0, g(1.1, 0.4)), 2),
            "was_fouled_pg": 0.0,
            "yellow_cards_pg": round(max(0, g(0.18, 0.08)), 3),
            "red_cards_pg": round(max(0, g(0.01, 0.02)), 3),
        }
    # Forward
    return {
        "appearances": appearances, "started": started,
        "minutes_pg": minutes_pg, "rating": rating,
        "goals": random.randint(4, 18),
        "assists": random.randint(2, 10),
        "shots_pg": round(max(0, g(2.8, 0.8)), 2),
        "shots_on_pg": round(max(0, g(1.2, 0.4)), 2),
        "passes_pg": round(g(28, 8), 1),
        "passes_accurate_pg": round(g(22, 6), 1),
        "pass_accuracy_pct": round(max(65, min(88, g(78, 5))), 1),
        "tackles_pg": round(max(0, g(0.5, 0.3)), 2),
        "interceptions_pg": round(max(0, g(0.4, 0.2)), 2),
        "fouls_pg": round(max(0, g(1.1, 0.4)), 2),
        "was_fouled_pg": 0.0,
        "yellow_cards_pg": round(max(0, g(0.16, 0.08)), 3),
        "red_cards_pg": round(max(0, g(0.02, 0.02)), 3),
    }


async def upsert_squad(session, team_id: int, squad: list[SeedPlayer]) -> None:
    # 1. Players
    player_rows = [
        {
            "id": p.id, "name": p.name, "nationality": p.nationality,
            "height_cm": p.height_cm,
            "photo_url": None,
            "firstname": p.name.split(" ", 1)[0],
            "lastname": p.name.split(" ", 1)[1] if " " in p.name else None,
        }
        for p in squad
    ]
    stmt = pg_insert(Player).values(player_rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Player.id],
        set_={
            "name": stmt.excluded.name,
            "nationality": stmt.excluded.nationality,
            "height_cm": stmt.excluded.height_cm,
        },
    )
    await session.execute(stmt)

    # 2. team_squads
    squad_rows = [
        {
            "team_id": team_id, "player_id": p.id,
            "league_id": LEAGUE_ID, "season_year": SEASON_YEAR,
            "shirt_number": p.shirt, "position": p.position, "is_active": True,
        }
        for p in squad
    ]
    stmt = pg_insert(TeamSquad).values(squad_rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[TeamSquad.team_id, TeamSquad.player_id, TeamSquad.season_year, TeamSquad.league_id],
        set_={
            "shirt_number": stmt.excluded.shirt_number,
            "position": stmt.excluded.position,
            "is_active": stmt.excluded.is_active,
        },
    )
    await session.execute(stmt)

    # 3. Per-player season stats
    stats_rows = []
    for p in squad:
        s = _stats_for(p.position)
        stats_rows.append({
            "player_id": p.id, "team_id": team_id,
            "league_id": LEAGUE_ID, "season_year": SEASON_YEAR,
            **s,
        })
    stmt = pg_insert(FootballPlayerSeasonStats).values(stats_rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[
            FootballPlayerSeasonStats.player_id,
            FootballPlayerSeasonStats.team_id,
            FootballPlayerSeasonStats.league_id,
            FootballPlayerSeasonStats.season_year,
        ],
        set_={k: getattr(stmt.excluded, k) for k in stats_rows[0].keys()
              if k not in {"player_id", "team_id", "league_id", "season_year"}},
    )
    await session.execute(stmt)


async def ensure_teams_exist(session) -> None:
    """Defensive: if smoke_test wasn't run, ensure the two teams exist."""
    rows = [
        {"id": HOME_TEAM, "name": "Smoke FC", "short_name": "SFC",
         "logo_url": "https://example.com/sfc.png"},
        {"id": AWAY_TEAM, "name": "Test United", "short_name": "TU",
         "logo_url": "https://example.com/tu.png"},
    ]
    stmt = pg_insert(Team).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Team.id],
        set_={"name": stmt.excluded.name, "short_name": stmt.excluded.short_name},
    )
    await session.execute(stmt)


async def main() -> None:
    random.seed(42)
    async with async_session_factory() as session:
        await ensure_teams_exist(session)
        await upsert_squad(session, HOME_TEAM, SMOKE_FC_SQUAD)
        await upsert_squad(session, AWAY_TEAM, TEST_UNITED_SQUAD)
        await session.commit()
        print(
            f"seeded squads: Smoke FC ({len(SMOKE_FC_SQUAD)} players), "
            f"Test United ({len(TEST_UNITED_SQUAD)} players)"
        )


if __name__ == "__main__":
    asyncio.run(main())
