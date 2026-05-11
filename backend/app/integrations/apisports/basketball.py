"""Basketball endpoints (NBA, Euroleague, BSL, BBL, ACB, Eurocup)."""
from __future__ import annotations

from typing import Optional

from app.core.config import settings
from app.integrations.apisports.base import APISportsClient


class BasketballClient(APISportsClient):
    def __init__(self) -> None:
        super().__init__(settings.APISPORTS_BASKETBALL_BASE, sport_label="basketball")

    async def leagues(self, season: str) -> Optional[list[dict]]:
        # Basketball uses string seasons like "2025-2026".
        return await self.get("leagues", {"season": season})

    async def games_by_date(self, league_id: int, season: str, date: str) -> Optional[list[dict]]:
        return await self.get("games", {
            "league": league_id, "season": season, "date": date,
        })

    async def games_by_team(self, team_id: int, season: str, last: int | None = None) -> Optional[list[dict]]:
        params: dict = {"team": team_id, "season": season}
        if last:
            params["last"] = last
        return await self.get("games", params)

    async def game_statistics(self, game_id: int) -> Optional[list[dict]]:
        return await self.get("games/statistics/teams", {"id": game_id})

    async def team_statistics(self, team_id: int, league_id: int, season: str) -> Optional[list[dict]]:
        return await self.get("teams/statistics", {
            "team": team_id, "league": league_id, "season": season,
        })

    async def standings(self, league_id: int, season: str) -> Optional[list[dict]]:
        return await self.get("standings", {"league": league_id, "season": season})

    async def players(self, team_id: int, season: str) -> Optional[list[dict]]:
        return await self.get("players", {"team": team_id, "season": season})

    async def player_statistics(self, player_id: int, season: str) -> Optional[list[dict]]:
        return await self.get("players/statistics", {"player": player_id, "season": season})
