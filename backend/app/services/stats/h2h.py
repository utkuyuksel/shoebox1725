"""Head-to-head — historical meetings between the two teams of a fixture.

Football pulls the full meeting history from api-sports' `fixtures/headtohead`
endpoint (works regardless of how many seasons we've loaded locally — the API
returns meetings across all seasons it has). Basketball has no h2h endpoint in
our integration, so it falls back to whatever finished fixtures we hold in the
DB (sport-agnostic score columns).

Either way the aggregate (W/D/L tally, average total) is expressed from the
fixture's home/away perspective regardless of who hosted the meeting.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Fixture
from app.integrations.apisports.football import FootballClient

_FINISHED = ("FT", "AET", "PEN")


@dataclass
class H2HMeeting:
    date: str                    # ISO date (YYYY-MM-DD)
    home_team_id: int            # who was home in *that* meeting
    away_team_id: int
    home_goals: Optional[int]    # goals (football) or points (basketball)
    away_goals: Optional[int]


@dataclass
class H2H:
    matches: int
    home_wins: int               # wins for the *fixture's* home team
    away_wins: int               # wins for the *fixture's* away team
    draws: int
    avg_total: Optional[float]   # avg combined score across decided meetings
    meetings: list[H2HMeeting]


async def compute_h2h(
    db: AsyncSession,
    home_team_id: int,
    away_team_id: int,
    sport: str = "football",
    *,
    limit: int = 10,
) -> H2H:
    if sport == "basketball":
        meetings = await _meetings_from_fixtures(db, home_team_id, away_team_id, limit)
    else:
        meetings = await _meetings_from_apisports(home_team_id, away_team_id, limit)
    return _aggregate(meetings, home_team_id, away_team_id)


# ---------------------------------------------------------------------------
# Football — api-sports
# ---------------------------------------------------------------------------

async def _meetings_from_apisports(
    home_team_id: int, away_team_id: int, limit: int
) -> list[H2HMeeting]:
    client = FootballClient()
    try:
        resp = await client.h2h(home_team_id, away_team_id)  # full history, no `last`
    finally:
        await client.close()
    if not resp:
        return []

    finished = [
        f for f in resp
        if ((f.get("fixture") or {}).get("status") or {}).get("short") in _FINISHED
    ]
    finished.sort(key=lambda f: (f.get("fixture") or {}).get("date") or "", reverse=True)

    out: list[H2HMeeting] = []
    for f in finished[:limit]:
        teams = f.get("teams") or {}
        goals = f.get("goals") or {}
        home = teams.get("home") or {}
        away = teams.get("away") or {}
        if home.get("id") is None or away.get("id") is None:
            continue
        date = ((f.get("fixture") or {}).get("date") or "")[:10]
        out.append(H2HMeeting(
            date=date,
            home_team_id=int(home["id"]),
            away_team_id=int(away["id"]),
            home_goals=goals.get("home"),
            away_goals=goals.get("away"),
        ))
    return out


# ---------------------------------------------------------------------------
# Basketball — local fixtures fallback
# ---------------------------------------------------------------------------

async def _meetings_from_fixtures(
    db: AsyncSession, home_team_id: int, away_team_id: int, limit: int
) -> list[H2HMeeting]:
    fxs = Fixture
    pair = or_(
        and_(fxs.home_team_id == home_team_id, fxs.away_team_id == away_team_id),
        and_(fxs.home_team_id == away_team_id, fxs.away_team_id == home_team_id),
    )
    rows = (await db.execute(
        select(fxs.kickoff_at, fxs.home_team_id, fxs.away_team_id, fxs.home_goals, fxs.away_goals)
        .where(pair, fxs.is_finished.is_(True))
        .order_by(fxs.kickoff_at.desc())
        .limit(limit)
    )).all()
    return [
        H2HMeeting(
            date=r.kickoff_at.date().isoformat(),
            home_team_id=r.home_team_id,
            away_team_id=r.away_team_id,
            home_goals=r.home_goals,
            away_goals=r.away_goals,
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Shared aggregate
# ---------------------------------------------------------------------------

def _aggregate(meetings: list[H2HMeeting], home_team_id: int, away_team_id: int) -> H2H:
    home_wins = away_wins = draws = 0
    totals: list[int] = []
    for m in meetings:
        if m.home_goals is None or m.away_goals is None:
            continue
        totals.append(m.home_goals + m.away_goals)
        if m.home_goals == m.away_goals:
            draws += 1
        else:
            winner = m.home_team_id if m.home_goals > m.away_goals else m.away_team_id
            if winner == home_team_id:
                home_wins += 1
            elif winner == away_team_id:
                away_wins += 1
    avg_total = round(sum(totals) / len(totals), 2) if totals else None
    return H2H(
        matches=len(meetings),
        home_wins=home_wins,
        away_wins=away_wins,
        draws=draws,
        avg_total=avg_total,
        meetings=meetings,
    )
