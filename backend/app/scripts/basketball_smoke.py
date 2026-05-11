"""Basketball end-to-end smoke seed: NBA-flavored fake teams + games + stats,
then recomputes aggregates so the mobile basketball preview has content.

Adds:
  - 2 fake teams (Smoke Hoops, Test Ballers)
  - 25 finished fixtures across season 2024, round "Regular Season"
  - 1 upcoming fixture tomorrow night
  - Per-fixture per-team BasketballFixtureTeamStats with realistic NBA ranges
  - BasketballTeamSeasonStats recomputed

Idempotent.

Run:
    python -m app.scripts.basketball_smoke
"""
from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.base import async_session_factory
from app.db.models import (
    BasketballFixtureTeamStats,
    BasketballTeamSeasonStats,
    Fixture,
    League,
    Season,
    Sport,
    Team,
)
from app.services.ingest.aggregates import (
    recompute_basketball_team_season_stats_for_league,
)
from app.services.ingest.seasons import ensure_season


log = logging.getLogger(__name__)


NBA_LEAGUE_ID = 12
SEASON_YEAR = 2024
ROUND_LABEL = "Regular Season"

HOME_TEAM = 9_900_003
AWAY_TEAM = 9_900_004
SYNTH_FIXTURE_BASE = 9_910_000      # different range than football synth
UPCOMING_FIXTURE_ID = 9_910_100
TARGET_FIXTURES = 25


async def wipe_synthetic(session) -> None:
    await session.execute(delete(BasketballFixtureTeamStats).where(
        BasketballFixtureTeamStats.fixture_id >= SYNTH_FIXTURE_BASE,
    ))
    await session.execute(delete(Fixture).where(Fixture.id >= SYNTH_FIXTURE_BASE))
    await session.execute(delete(BasketballTeamSeasonStats).where(
        BasketballTeamSeasonStats.team_id.in_([HOME_TEAM, AWAY_TEAM]),
    ))
    await session.execute(delete(Team).where(Team.id.in_([HOME_TEAM, AWAY_TEAM])))


async def ensure_league_and_teams(session) -> None:
    # Ensure sport + league exist (seed_leagues might not have run)
    sport_id = (await session.execute(
        select(Sport.id).where(Sport.code == "basketball")
    )).scalar_one_or_none()
    if sport_id is None:
        sport = Sport(code="basketball", name="Basketball")
        session.add(sport)
        await session.flush()
        sport_id = sport.id

    exists = (await session.execute(
        select(League.id).where(League.id == NBA_LEAGUE_ID)
    )).scalar_one_or_none()
    if exists is None:
        session.add(League(
            id=NBA_LEAGUE_ID, sport_id=sport_id,
            name="NBA", country="USA", country_code="US",
            is_active=True, is_default_popular=True,
            sort_order=101, is_free_tier=True,
        ))

    # Teams
    teams = [
        {"id": HOME_TEAM, "name": "Smoke Hoops", "short_name": "SHP",
         "logo_url": "https://example.com/shp.png", "country": "USA"},
        {"id": AWAY_TEAM, "name": "Test Ballers", "short_name": "TBL",
         "logo_url": "https://example.com/tbl.png", "country": "USA"},
    ]
    stmt = pg_insert(Team).values(teams)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Team.id],
        set_={"name": stmt.excluded.name, "short_name": stmt.excluded.short_name},
    )
    await session.execute(stmt)


def _team_stats(scale: float, points: int) -> dict:
    """Realistic NBA-ish per-team per-game stats. `points` is the final score."""
    g = random.gauss
    fg_made = max(20, int(g(points / 2.4, 4)))   # most points come from FG
    fg_att = max(fg_made + 20, int(g(85 * scale, 6)))
    three_made = max(2, int(g(13 * scale, 3)))
    three_att = max(three_made + 5, int(g(35 * scale, 4)))
    two_made = max(0, fg_made - three_made)
    two_att = max(two_made, fg_att - three_att)
    ft_made = max(0, points - (3 * three_made + 2 * two_made))
    ft_att = max(ft_made, int(g(22, 3)))
    return {
        "points": points,
        "field_goals_made": fg_made,
        "field_goals_att": fg_att,
        "two_points_made": two_made,
        "two_points_att": two_att,
        "three_points_made": three_made,
        "three_points_att": three_att,
        "free_throws_made": ft_made,
        "free_throws_att": ft_att,
        "rebounds_offensive": max(0, int(g(10, 2))),
        "rebounds_defensive": max(0, int(g(33, 4))),
        "assists": max(0, int(g(25, 4))),
        "steals": max(0, int(g(7.5, 2))),
        "blocks": max(0, int(g(5, 1.5))),
        "turnovers": max(0, int(g(13, 3))),
        "fouls": max(0, int(g(19, 3))),
    }


async def seed_fixtures_and_stats(session) -> None:
    base_kickoff = datetime(2024, 10, 22, 0, 30, tzinfo=timezone.utc)
    for i in range(TARGET_FIXTURES):
        # Home advantage: home team usually scores more.
        home_pts = max(85, int(random.gauss(116, 9)))
        away_pts = max(85, int(random.gauss(108, 9)))
        # Avoid ties in basketball
        if home_pts == away_pts:
            home_pts += 1

        fixture_id = SYNTH_FIXTURE_BASE + i
        kickoff = base_kickoff + timedelta(days=i * 3)

        await session.execute(pg_insert(Fixture).values(
            id=fixture_id,
            league_id=NBA_LEAGUE_ID,
            season_year=SEASON_YEAR,
            round=ROUND_LABEL,
            home_team_id=HOME_TEAM,
            away_team_id=AWAY_TEAM,
            kickoff_at=kickoff,
            status="FT",
            home_goals=home_pts,
            away_goals=away_pts,
            venue="Smoke Arena",
        ).on_conflict_do_update(
            index_elements=[Fixture.id],
            set_={"home_goals": home_pts, "away_goals": away_pts, "status": "FT"},
        ))

        for team_id, scale, pts in [
            (HOME_TEAM, 1.05, home_pts),
            (AWAY_TEAM, 0.95, away_pts),
        ]:
            stats = _team_stats(scale, pts)
            await session.execute(pg_insert(BasketballFixtureTeamStats).values(
                fixture_id=fixture_id, team_id=team_id,
                is_home=team_id == HOME_TEAM, **stats,
            ).on_conflict_do_update(
                index_elements=[BasketballFixtureTeamStats.fixture_id, BasketballFixtureTeamStats.team_id],
                set_=stats,
            ))


async def upsert_upcoming(session) -> None:
    kickoff = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=2, minute=30, second=0, microsecond=0,
    )
    stmt = pg_insert(Fixture).values(
        id=UPCOMING_FIXTURE_ID,
        league_id=NBA_LEAGUE_ID,
        season_year=SEASON_YEAR,
        round=ROUND_LABEL,
        home_team_id=HOME_TEAM,
        away_team_id=AWAY_TEAM,
        kickoff_at=kickoff,
        status="NS",
        venue="Smoke Arena",
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[Fixture.id],
        set_={"kickoff_at": stmt.excluded.kickoff_at, "status": "NS",
              "round": stmt.excluded.round},
    )
    await session.execute(stmt)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    random.seed(73)

    async with async_session_factory() as session:
        # Wipe first so old fixtures/teams don't block re-creates.
        await wipe_synthetic(session)
        await session.commit()

        # Now re-create league + teams.
        await ensure_league_and_teams(session)
        await session.commit()

        await ensure_season(session, NBA_LEAGUE_ID, SEASON_YEAR,
                            is_current=True, current_round=ROUND_LABEL)
        await seed_fixtures_and_stats(session)
        await upsert_upcoming(session)
        await session.commit()

        teams = await recompute_basketball_team_season_stats_for_league(
            session, NBA_LEAGUE_ID, SEASON_YEAR,
        )
        await session.commit()
        log.info("basketball_seed_done teams_recomputed=%d fixtures=%d (+1 upcoming)",
                 teams, TARGET_FIXTURES)
        print(f"DONE: NBA seeded — upcoming fixture id={UPCOMING_FIXTURE_ID}")


if __name__ == "__main__":
    asyncio.run(main())
