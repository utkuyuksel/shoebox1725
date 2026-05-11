"""End-to-end smoke test with synthetic data.

Spends zero api-sports quota. Creates two fake teams, three fake referees,
and 20 fake fixtures with realistic statistics, then exercises the full
pipeline: ingest → aggregate recompute → match preview JSON.

Use this to:
- Confirm DB + models + migrations are wired correctly.
- Eyeball the shape of /v1/match/{id} before spending real quota.
- Iterate on hit-rate / trend / insight rules without rate-limit pressure.

Run:
    python -m app.scripts.smoke_test

Idempotent: rerun wipes the synthetic rows (IDs in a reserved range) and
recreates them. Production data with normal ids is untouched.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.base import async_session_factory
from app.db.models import (
    Fixture,
    FootballFixtureTeamStats,
    FootballTeamSeasonStats,
    League,
    Referee,
    RefereeSeasonStats,
    RefereeTeamHistory,
    Sport,
    Team,
)
from app.services.ingest.aggregates import (
    recompute_football_team_season_stats_for_league,
    recompute_referee_aggregates_for_league,
    recompute_referee_team_history,
)
from app.services.ingest.fixture_stats import ingest_football_fixture_stats
from app.services.ingest.fixtures import upsert_fixture
from app.services.ingest.seasons import ensure_season
from app.services.match_preview import build_match_preview


log = logging.getLogger(__name__)


# Reserved synthetic id range — high enough that real api-sports IDs won't collide.
SYNTH_TEAM_HOME = 9_900_001
SYNTH_TEAM_AWAY = 9_900_002
SYNTH_LEAGUE_ID = 9_999_999          # use a real league id from seed instead
SYNTH_SEASON_YEAR = 2024
SYNTH_FIXTURE_BASE = 9_900_000

# Real Süper Lig id from seed — match preview will look for league=203.
REAL_LEAGUE_ID = 203
TARGET_FIXTURES = 20


_HOME_TEAM = {
    "id": SYNTH_TEAM_HOME, "name": "Smoke FC", "short_name": "SFC",
    "logo": "https://example.com/sfc.png",
}
_AWAY_TEAM = {
    "id": SYNTH_TEAM_AWAY, "name": "Test United", "short_name": "TU",
    "logo": "https://example.com/tu.png",
}

# Three referees we cycle through, so referee-team aggregates have real data.
_REFEREES = ["Halil Umut Meler", "Felix Brych", "Michael Oliver"]


async def wipe_synthetic_data(session) -> None:
    """Remove any synthetic rows from a previous run.

    Order matters — child rows first so FKs don't block parent deletes.
    """
    await session.execute(delete(FootballFixtureTeamStats).where(
        FootballFixtureTeamStats.fixture_id >= SYNTH_FIXTURE_BASE,
    ))
    await session.execute(delete(Fixture).where(Fixture.id >= SYNTH_FIXTURE_BASE))
    await session.execute(delete(FootballTeamSeasonStats).where(
        FootballTeamSeasonStats.team_id.in_([SYNTH_TEAM_HOME, SYNTH_TEAM_AWAY]),
    ))
    # referee_team_history references teams; clear those rows before deleting teams.
    await session.execute(delete(RefereeTeamHistory).where(
        RefereeTeamHistory.team_id.in_([SYNTH_TEAM_HOME, SYNTH_TEAM_AWAY]),
    ))
    await session.execute(delete(Team).where(Team.id.in_([SYNTH_TEAM_HOME, SYNTH_TEAM_AWAY])))
    # Don't wipe referees globally — they may be shared with real data.
    # We just wipe ref aggregates the recompute would have written for our
    # synthetic league.
    await session.execute(delete(RefereeSeasonStats).where(
        RefereeSeasonStats.league_id == REAL_LEAGUE_ID,
        RefereeSeasonStats.season_year == SYNTH_SEASON_YEAR,
    ))


async def ensure_sport_and_league(session) -> None:
    """Make sure the foreign-key targets exist."""
    # sport
    sport = (await session.execute(select(Sport).where(Sport.code == "football"))).scalar_one_or_none()
    if sport is None:
        sport = Sport(code="football", name="Football")
        session.add(sport)
        await session.flush()

    # league
    league = (await session.execute(select(League).where(League.id == REAL_LEAGUE_ID))).scalar_one_or_none()
    if league is None:
        session.add(League(
            id=REAL_LEAGUE_ID, sport_id=sport.id,
            name="Süper Lig", country="Turkey", country_code="TR",
            is_active=True, is_default_popular=True, sort_order=6, is_free_tier=False,
        ))
        await session.flush()


def _build_fake_payload(idx: int, base_kickoff: datetime) -> dict:
    """Build a single api-sports-shaped fixture payload."""
    is_home_win = idx % 3 != 0
    home_goals = random.randint(1, 3) if is_home_win else random.randint(0, 2)
    away_goals = random.randint(0, 2) if is_home_win else random.randint(1, 3)
    if home_goals == away_goals and idx % 2:
        home_goals += 1

    referee = _REFEREES[idx % len(_REFEREES)]
    kickoff = base_kickoff + timedelta(days=idx * 7)

    return {
        "fixture": {
            "id": SYNTH_FIXTURE_BASE + idx,
            "referee": f"{referee}, Turkey",
            "date": kickoff.isoformat(),
            "status": {"short": "FT"},
            "venue": {"name": "Smoke Arena"},
        },
        "league": {
            "id": REAL_LEAGUE_ID,
            "season": SYNTH_SEASON_YEAR,
            "round": f"Regular Season - {idx + 1}",
        },
        "teams": {
            "home": _HOME_TEAM,
            "away": _AWAY_TEAM,
        },
        "goals": {"home": home_goals, "away": away_goals},
        "score": {"halftime": {"home": max(0, home_goals - 1), "away": max(0, away_goals - 1)}},
    }


def _build_fake_stats(fixture_id: int, home_team_id: int, away_team_id: int) -> list[dict]:
    """Build an api-sports /fixtures/statistics-shaped payload."""
    def team_stats(team_id: int, scale: float) -> dict:
        return {
            "team": {"id": team_id, "name": "team"},
            "statistics": [
                {"type": "Total Shots",     "value": int(random.gauss(13 * scale, 3))},
                {"type": "Shots on Goal",   "value": int(random.gauss(5 * scale, 2))},
                {"type": "Shots off Goal",  "value": int(random.gauss(5 * scale, 2))},
                {"type": "Blocked Shots",   "value": int(random.gauss(3, 1))},
                {"type": "Corner Kicks",    "value": int(random.gauss(5.5 * scale, 1.5))},
                {"type": "Fouls",           "value": int(random.gauss(12, 3))},
                {"type": "Offsides",        "value": int(random.gauss(2, 1))},
                {"type": "Yellow Cards",    "value": int(random.gauss(2.2, 1))},
                {"type": "Red Cards",       "value": 1 if random.random() < 0.05 else 0},
                {"type": "Goalkeeper Saves", "value": int(random.gauss(3, 1.5))},
                {"type": "Ball Possession", "value": f"{int(50 + random.gauss(0, 8) * scale)}%"},
                {"type": "Total passes",    "value": int(random.gauss(450 * scale, 80))},
                {"type": "Passes accurate", "value": int(random.gauss(370 * scale, 70))},
                {"type": "Passes %",        "value": int(random.gauss(82, 4))},
                {"type": "expected_goals",  "value": round(random.gauss(1.4 * scale, 0.4), 2)},
            ],
        }

    return [
        team_stats(home_team_id, scale=1.1),  # home advantage
        team_stats(away_team_id, scale=0.9),
    ]


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    random.seed(42)  # deterministic output → easier diffs across runs

    async with async_session_factory() as session:
        await ensure_sport_and_league(session)
        await session.commit()

        await wipe_synthetic_data(session)
        await session.commit()

        await ensure_season(session, REAL_LEAGUE_ID, SYNTH_SEASON_YEAR, is_current=False)

        # Generate fixtures spread across 20 weeks of a past season.
        base_kickoff = datetime(2024, 8, 18, 18, 0, tzinfo=timezone.utc)
        for i in range(TARGET_FIXTURES):
            payload = _build_fake_payload(i, base_kickoff)
            fid = await upsert_fixture(session, payload)
            if fid is None:
                continue
            stats_payload = _build_fake_stats(fid, SYNTH_TEAM_HOME, SYNTH_TEAM_AWAY)
            await ingest_football_fixture_stats(session, fid, stats_payload)
        await session.commit()
        log.info("smoke_ingested fixtures=%d", TARGET_FIXTURES)

        # Recompute everything.
        teams_done = await recompute_football_team_season_stats_for_league(
            session, REAL_LEAGUE_ID, SYNTH_SEASON_YEAR,
        )
        await recompute_referee_aggregates_for_league(
            session, REAL_LEAGUE_ID, SYNTH_SEASON_YEAR,
        )
        await recompute_referee_team_history(session)
        await session.commit()
        log.info("smoke_aggregates_done teams_recomputed=%d", teams_done)

        # Pick the most recent finished fixture and render its match preview.
        latest = (await session.execute(
            select(Fixture).where(Fixture.id >= SYNTH_FIXTURE_BASE).order_by(Fixture.kickoff_at.desc()).limit(1)
        )).scalar_one()
        preview = await build_match_preview(session, latest)

        print("\n===== /v1/match/%d preview =====" % latest.id)
        print(json.dumps(preview, indent=2, default=str))
        print("\n===== summary =====")
        print(f"fixtures: {TARGET_FIXTURES}")
        print(f"teams_recomputed: {teams_done}")
        print(f"insights: {len(preview.get('insights') or [])}")
        print(f"home season_stats.played: {(preview['home'].get('season_stats') or {}).get('played')}")
        print(f"away season_stats.played: {(preview['away'].get('season_stats') or {}).get('played')}")
        print(f"referee assigned: {bool(preview.get('referee'))}")
        if preview.get("referee"):
            print(f"  ref name: {preview['referee']['name']}")
            vh = preview["referee"].get("vs_home_team") or {}
            print(f"  ref vs home: {vh.get('matches')} matches, {vh.get('yellow_cards_pg')} ycards/g")


if __name__ == "__main__":
    asyncio.run(main())
