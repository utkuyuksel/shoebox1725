"""Player profile endpoint — season stats for football or basketball."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import DBSession
from app.db.models import (
    BasketballPlayerSeasonStats,
    FootballPlayerSeasonStats,
    Player,
)


router = APIRouter(tags=["players"])


@router.get("/players/{player_id}")
async def player_profile(
    player_id: int,
    db: DBSession,
    league_id: int = Query(...),
    season: int = Query(...),
    sport: str = Query(..., description="football | basketball"),
):
    player = (await db.execute(
        select(Player).where(Player.id == player_id)
    )).scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="player not found")

    if sport == "football":
        stats = (await db.execute(
            select(FootballPlayerSeasonStats).where(
                FootballPlayerSeasonStats.player_id == player_id,
                FootballPlayerSeasonStats.league_id == league_id,
                FootballPlayerSeasonStats.season_year == season,
            )
        )).scalar_one_or_none()
        stats_payload = _serialize_football_player(stats) if stats else None
    elif sport == "basketball":
        stats = (await db.execute(
            select(BasketballPlayerSeasonStats).where(
                BasketballPlayerSeasonStats.player_id == player_id,
                BasketballPlayerSeasonStats.league_id == league_id,
                BasketballPlayerSeasonStats.season_year == season,
            )
        )).scalar_one_or_none()
        stats_payload = _serialize_basketball_player(stats) if stats else None
    else:
        raise HTTPException(status_code=400, detail="sport must be 'football' or 'basketball'")

    return {
        "player": {
            "id": player.id,
            "name": player.name,
            "photo": player.photo_url,
            "nationality": player.nationality,
            "birth_date": player.birth_date.isoformat() if player.birth_date else None,
            "height_cm": player.height_cm,
            "weight_kg": player.weight_kg,
        },
        "stats": stats_payload,
    }


def _serialize_football_player(s: FootballPlayerSeasonStats) -> dict:
    return {
        "appearances": s.appearances,
        "started": s.started,
        "minutes_pg": _f(s.minutes_pg),
        "rating": _f(s.rating),
        "goals": s.goals,
        "assists": s.assists,
        "shots_pg": _f(s.shots_pg),
        "shots_on_pg": _f(s.shots_on_pg),
        "passes_pg": _f(s.passes_pg),
        "passes_accurate_pg": _f(s.passes_accurate_pg),
        "pass_accuracy_pct": _f(s.pass_accuracy_pct),
        "tackles_pg": _f(s.tackles_pg),
        "interceptions_pg": _f(s.interceptions_pg),
        "fouls_pg": _f(s.fouls_pg),
        "yellow_cards_pg": _f(s.yellow_cards_pg),
        "red_cards_pg": _f(s.red_cards_pg),
    }


def _serialize_basketball_player(s: BasketballPlayerSeasonStats) -> dict:
    return {
        "appearances": s.appearances,
        "minutes_pg": _f(s.minutes_pg),
        "points_pg": _f(s.points_pg),
        "rebounds_pg": _f(s.rebounds_pg),
        "assists_pg": _f(s.assists_pg),
        "steals_pg": _f(s.steals_pg),
        "blocks_pg": _f(s.blocks_pg),
        "turnovers_pg": _f(s.turnovers_pg),
        "fg": {"made": _f(s.fg_made_pg), "att": _f(s.fg_att_pg), "pct": _f(s.fg_pct)},
        "two": {"made": _f(s.two_made_pg), "att": _f(s.two_att_pg), "pct": _f(s.two_pct)},
        "three": {"made": _f(s.three_made_pg), "att": _f(s.three_att_pg), "pct": _f(s.three_pct)},
        "ft": {"made": _f(s.ft_made_pg), "att": _f(s.ft_att_pg), "pct": _f(s.ft_pct)},
    }


def _f(x) -> float | None:
    return float(x) if x is not None else None
