"""Referee search + profile."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import aliased

from app.api.deps import DBSession
from app.db.models import (
    Fixture,
    FootballFixtureTeamStats,
    Referee,
    RefereeSeasonStats,
    Team,
)


router = APIRouter(tags=["referees"])


@router.get("/referees/search")
async def search_referees(db: DBSession, q: str = Query(..., min_length=2)):
    # pg_trgm fuzzy match on name; ordered by similarity.
    # Explicit ::text casts keep asyncpg's prepared-statement param inference happy.
    sql = text("""
        SELECT id, name, nationality, photo_url, public.similarity(name::text, :q ::text) AS sim
        FROM referees
        WHERE name::text OPERATOR(public.%) :q ::text
        ORDER BY sim DESC
        LIMIT 15
    """)
    rows = (await db.execute(sql, {"q": q})).all()
    return {
        "results": [
            {"id": r.id, "name": r.name, "nationality": r.nationality, "photo": r.photo_url}
            for r in rows
        ]
    }


@router.get("/referees/{referee_id}")
async def referee_profile(
    referee_id: int,
    db: DBSession,
    season: int = Query(...),
):
    ref = (await db.execute(
        select(Referee).where(Referee.id == referee_id)
    )).scalar_one_or_none()
    if ref is None:
        raise HTTPException(status_code=404, detail="referee not found")

    # Per-league season aggregates for this referee + season.
    season_rows = (await db.execute(
        select(RefereeSeasonStats).where(
            RefereeSeasonStats.referee_id == referee_id,
            RefereeSeasonStats.season_year == season,
        )
    )).scalars().all()

    # Last 5 finished matches this referee officiated, with summed cards.
    HomeTeam = aliased(Team)
    AwayTeam = aliased(Team)
    fixture_rows = (await db.execute(
        select(Fixture, HomeTeam, AwayTeam)
        .join(HomeTeam, HomeTeam.id == Fixture.home_team_id)
        .join(AwayTeam, AwayTeam.id == Fixture.away_team_id)
        .where(Fixture.referee_id == referee_id, Fixture.is_finished.is_(True))
        .order_by(Fixture.kickoff_at.desc())
        .limit(5)
    )).all()

    fixture_ids = [fx.id for (fx, _h, _a) in fixture_rows]
    card_map: dict[int, tuple[int, int]] = {}
    if fixture_ids:
        card_rows = (await db.execute(
            select(
                FootballFixtureTeamStats.fixture_id,
                func.coalesce(func.sum(FootballFixtureTeamStats.yellow_cards), 0).label("yc"),
                func.coalesce(func.sum(FootballFixtureTeamStats.red_cards), 0).label("rc"),
            )
            .where(FootballFixtureTeamStats.fixture_id.in_(fixture_ids))
            .group_by(FootballFixtureTeamStats.fixture_id)
        )).all()
        card_map = {r.fixture_id: (int(r.yc or 0), int(r.rc or 0)) for r in card_rows}

    last_matches = [
        {
            "id": fx.id,
            "league_id": fx.league_id,
            "season": fx.season_year,
            "kickoff_at": fx.kickoff_at.isoformat(),
            "home": {"id": h.id, "name": h.name, "goals": fx.home_goals, "logo": h.logo_url},
            "away": {"id": a.id, "name": a.name, "goals": fx.away_goals, "logo": a.logo_url},
            "yellow_cards": card_map.get(fx.id, (0, 0))[0],
            "red_cards":    card_map.get(fx.id, (0, 0))[1],
        }
        for (fx, h, a) in fixture_rows
    ]

    return {
        "referee": {
            "id": ref.id,
            "name": ref.name,
            "nationality": ref.nationality,
            "photo": ref.photo_url,
        },
        "season_stats": [
            {
                "league_id": s.league_id,
                "matches": s.matches,
                "yellow_cards_pg": float(s.yellow_cards_pg) if s.yellow_cards_pg else None,
                "red_cards_pg": float(s.red_cards_pg) if s.red_cards_pg else None,
                "fouls_pg": float(s.fouls_pg) if s.fouls_pg else None,
                "penalties_pg": float(s.penalties_pg) if s.penalties_pg else None,
                "home_win_pct": float(s.home_win_pct) if s.home_win_pct else None,
            }
            for s in season_rows
        ],
        "last_matches": last_matches,
    }
