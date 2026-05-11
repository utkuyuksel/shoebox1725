"""Insert one upcoming fixture into Süper Lig so the mobile app has
something to click. Reuses Smoke FC / Test United (synthetic teams) and a
referee already in the DB, so the match preview shows aggregates and
ref-team history out of the box.

Idempotent: re-running just updates the kickoff time forward.

Run:
    python -m app.scripts.add_upcoming_fixture
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.base import async_session_factory
from app.db.models import Fixture, Referee, Season


LEAGUE_ID = 203                # Süper Lig
SEASON_YEAR = 2024
ROUND_LABEL = "Regular Season - 30"
HOME_TEAM_ID = 9_900_001       # Smoke FC
AWAY_TEAM_ID = 9_900_002       # Test United
UPCOMING_FIXTURE_ID = 9_900_100


async def main() -> None:
    async with async_session_factory() as s:
        # 1. Mark the season as current so the fixtures endpoint finds it.
        season = (await s.execute(
            select(Season).where(Season.league_id == LEAGUE_ID, Season.year == SEASON_YEAR)
        )).scalar_one()
        season.is_current = True
        season.current_round = ROUND_LABEL

        # 2. Pick any referee we have so the ref card lights up.
        ref = (await s.execute(select(Referee).limit(1))).scalar_one_or_none()
        ref_id = ref.id if ref else None
        ref_name = ref.name if ref else "<none>"

        # 3. Upsert the fixture. Kickoff = tomorrow 21:00 local.
        kickoff = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
            hour=21, minute=0, second=0, microsecond=0,
        )

        stmt = pg_insert(Fixture).values(
            id=UPCOMING_FIXTURE_ID,
            league_id=LEAGUE_ID,
            season_year=SEASON_YEAR,
            round=ROUND_LABEL,
            home_team_id=HOME_TEAM_ID,
            away_team_id=AWAY_TEAM_ID,
            kickoff_at=kickoff,
            status="NS",
            home_goals=None,
            away_goals=None,
            referee_id=ref_id,
            venue="Shoebox Demo Arena",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[Fixture.id],
            set_={
                "round": stmt.excluded.round,
                "kickoff_at": stmt.excluded.kickoff_at,
                "status": stmt.excluded.status,
                "referee_id": stmt.excluded.referee_id,
                "home_team_id": stmt.excluded.home_team_id,
                "away_team_id": stmt.excluded.away_team_id,
            },
        )
        await s.execute(stmt)
        await s.commit()

        print(
            f"upcoming fixture {UPCOMING_FIXTURE_ID} → "
            f"Süper Lig | {ROUND_LABEL} | kickoff {kickoff.isoformat()} | ref={ref_name}"
        )


if __name__ == "__main__":
    asyncio.run(main())
