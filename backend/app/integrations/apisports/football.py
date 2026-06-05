"""Football endpoints we need. Thin wrappers — no business logic here."""
from __future__ import annotations

from typing import Optional

from app.core.config import settings
from app.integrations.apisports.base import APISportsClient


class FootballClient(APISportsClient):
    def __init__(self) -> None:
        super().__init__(settings.APISPORTS_FOOTBALL_BASE, sport_label="football")

    async def leagues(self, season: int) -> Optional[list[dict]]:
        return await self.get("leagues", {"season": season})

    async def current_round(self, league_id: int, season: int) -> Optional[str]:
        data = await self.get("fixtures/rounds", {
            "league": league_id, "season": season, "current": "true",
        })
        if not data:
            return None
        return data[0] if isinstance(data, list) and data else None

    async def fixtures_for_round(self, league_id: int, season: int, round_: str,
                                 tz: str = "Europe/Istanbul") -> Optional[list[dict]]:
        return await self.get("fixtures", {
            "league": league_id, "season": season, "round": round_, "timezone": tz,
        })

    async def fixture(self, fixture_id: int) -> Optional[list[dict]]:
        return await self.get("fixtures", {"id": fixture_id})

    async def fixture_statistics(self, fixture_id: int) -> Optional[list[dict]]:
        return await self.get("fixtures/statistics", {"fixture": fixture_id})

    async def team_fixtures(self, team_id: int, season: int, last: int | None = None) -> Optional[list[dict]]:
        params: dict = {"team": team_id, "season": season}
        if last:
            params["last"] = last
        return await self.get("fixtures", params)

    async def h2h(self, team_a: int, team_b: int, last: int | None = None) -> Optional[list[dict]]:
        # NB: the `last` parameter requires a paid api-sports plan. Omit it by
        # default and slice client-side — the plain call returns full history.
        params: dict = {"h2h": f"{team_a}-{team_b}"}
        if last:
            params["last"] = last
        return await self.get("fixtures/headtohead", params)

    async def squad(self, team_id: int) -> Optional[list[dict]]:
        return await self.get("players/squads", {"team": team_id})

    async def player_stats(self, player_id: int, season: int) -> Optional[list[dict]]:
        return await self.get("players", {"id": player_id, "season": season})

    async def players_by_team(self, team_id: int, season: int, page: int = 1) -> Optional[list[dict]]:
        return await self.get("players", {"team": team_id, "season": season, "page": page})

    async def team_statistics(self, team_id: int, league_id: int, season: int) -> Optional[list[dict]]:
        return await self.get("teams/statistics", {
            "team": team_id, "league": league_id, "season": season,
        })

    async def standings(self, league_id: int, season: int) -> Optional[list[dict]]:
        return await self.get("standings", {"league": league_id, "season": season})

    async def injuries(self, league_id: int, season: int) -> Optional[list[dict]]:
        return await self.get("injuries", {"league": league_id, "season": season})

    async def lineups(self, fixture_id: int) -> Optional[list[dict]]:
        return await self.get("fixtures/lineups", {"fixture": fixture_id})
