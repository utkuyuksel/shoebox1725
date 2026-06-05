"""League standings — fetched ready-made from api-sports.

We pull the official table straight from api-sports' `/standings` endpoint
instead of deriving it from our fixtures: the source table is already scoped
to the real competition (no preseason / All-Star / exhibition noise that the
raw NBA fixtures carry) and carries points, rank, and form. The API response
is reshaped into our own flat, sport-aware payload so the mobile client stays
unchanged. Results are cached at the API layer (Redis).

Football: one group per league, ranked by the source. Basketball: api-sports
returns rows grouped by conference/division (a team can appear more than
once) — we dedupe to one row per team and re-rank league-wide by win%.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Fixture, League, Sport
from app.integrations.apisports.basketball import BasketballClient
from app.integrations.apisports.football import FootballClient


async def _sport_for_league(db: AsyncSession, league_id: int) -> str:
    row = (await db.execute(
        select(Sport.code).join(League, League.sport_id == Sport.id).where(League.id == league_id)
    )).scalar_one_or_none()
    return row or "football"


async def _latest_season(db: AsyncSession, league_id: int) -> Optional[int]:
    return (await db.execute(
        select(func.max(Fixture.season_year)).where(Fixture.league_id == league_id)
    )).scalar_one_or_none()


async def compute_standings(
    db: AsyncSession,
    league_id: int,
    season: Optional[int] = None,
) -> dict:
    sport = await _sport_for_league(db, league_id)
    if season is None:
        season = await _latest_season(db, league_id)
    empty = {"league_id": league_id, "season": season, "sport": sport, "rows": []}
    if season is None:
        return empty

    if sport == "basketball":
        rows = await _basketball_standings(league_id, season)
    else:
        rows = await _football_standings(league_id, season)

    return {"league_id": league_id, "season": season, "sport": sport, "rows": rows}


# ---------------------------------------------------------------------------
# Football
# ---------------------------------------------------------------------------

async def _football_standings(league_id: int, season: int) -> list[dict]:
    client = FootballClient()
    try:
        resp = await client.standings(league_id, season)
    finally:
        await client.close()
    if not resp:
        return []

    # response[0].league.standings = [[row, row, ...], ...]  (groups)
    groups = (resp[0].get("league") or {}).get("standings") or []
    out: list[dict] = []
    for group in groups:
        for r in group:
            alls = r.get("all") or {}
            goals = alls.get("goals") or {}
            gf = _i(goals.get("for"))
            ga = _i(goals.get("against"))
            out.append({
                "rank": _i(r.get("rank")),
                "team_id": _team_id(r),
                "name": (r.get("team") or {}).get("name"),
                "short_name": None,
                "logo": (r.get("team") or {}).get("logo"),
                "played": _i(alls.get("played")),
                "wins": _i(alls.get("win")),
                "draws": _i(alls.get("draw")),
                "losses": _i(alls.get("lose")),
                "points_for": gf,
                "points_against": ga,
                "diff": _i(r.get("goalsDiff"), default=(gf - ga) if gf is not None and ga is not None else 0),
                "points": _i(r.get("points")),
                "win_pct": None,
                "form": _form(r.get("form")),
            })
    return out


# ---------------------------------------------------------------------------
# Basketball
# ---------------------------------------------------------------------------

async def _basketball_standings(league_id: int, season: int) -> list[dict]:
    # api-sports basketball uses string seasons like "2024-2025".
    season_str = f"{season}-{season + 1}"
    client = BasketballClient()
    try:
        resp = await client.standings(league_id, season_str)
    finally:
        await client.close()
    if not resp:
        return []

    # response is a list of groups (each a list of rows); a team can appear in
    # more than one grouping (conference + division) → dedupe by team id.
    by_team: dict[int, dict] = {}
    for group in resp:
        rows = group if isinstance(group, list) else [group]
        for r in rows:
            team = r.get("team") or {}
            tid = _i(team.get("id"))
            if tid is None or tid in by_team:
                continue
            games = r.get("games") or {}
            win = games.get("win") or {}
            lose = games.get("lose") or {}
            pts = r.get("points") or {}
            pf = _i(pts.get("for"))
            pa = _i(pts.get("against"))
            by_team[tid] = {
                "team_id": tid,
                "name": team.get("name"),
                "short_name": None,
                "logo": team.get("logo"),
                "played": _i(games.get("played")),
                "wins": _i(win.get("total")),
                "draws": None,
                "losses": _i(lose.get("total")),
                "points_for": pf,
                "points_against": pa,
                "diff": (pf - pa) if pf is not None and pa is not None else 0,
                "points": None,
                "win_pct": _f(win.get("percentage")),
                "form": _form(r.get("form")),
            }

    ordered = sorted(by_team.values(), key=lambda x: -(x["win_pct"] or 0.0))
    for rank, row in enumerate(ordered, start=1):
        row["rank"] = rank
    return ordered


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _team_id(row: dict) -> Optional[int]:
    return _i((row.get("team") or {}).get("id"))


def _form(form: Optional[str], last: int = 5) -> list[str]:
    if not form:
        return []
    return [c for c in form if c in ("W", "D", "L")][-last:]


def _i(v, default: Optional[int] = None) -> Optional[int]:
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _f(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return round(float(v), 3)
    except (TypeError, ValueError):
        return None
