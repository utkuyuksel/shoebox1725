from fastapi import APIRouter

from app.api.v1 import fixtures, leagues, match, players, referees, standings, teams, watchlist


api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(leagues.router)
api_v1_router.include_router(standings.router)
api_v1_router.include_router(fixtures.router)
api_v1_router.include_router(match.router)
api_v1_router.include_router(teams.router)
api_v1_router.include_router(players.router)
api_v1_router.include_router(referees.router)
api_v1_router.include_router(watchlist.router)
