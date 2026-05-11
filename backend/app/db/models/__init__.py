"""Import every model so Alembic / Base.metadata can see them."""
from app.db.models.catalog import League, Season, Sport
from app.db.models.fixtures import (
    BasketballFixtureTeamStats,
    Fixture,
    FootballFixtureTeamStats,
)
from app.db.models.insights import FixtureInsight
from app.db.models.operational import RefreshLog
from app.db.models.referees import Referee, RefereeAlias, RefereeSeasonStats, RefereeTeamHistory
from app.db.models.season_stats import (
    BasketballPlayerSeasonStats,
    BasketballTeamSeasonStats,
    FootballPlayerSeasonStats,
    FootballTeamSeasonStats,
)
from app.db.models.teams import Player, Team, TeamSquad
from app.db.models.users import User, UserWatchlistFixture


__all__ = [
    "BasketballFixtureTeamStats",
    "BasketballPlayerSeasonStats",
    "BasketballTeamSeasonStats",
    "Fixture",
    "FixtureInsight",
    "FootballFixtureTeamStats",
    "FootballPlayerSeasonStats",
    "FootballTeamSeasonStats",
    "League",
    "Player",
    "Referee",
    "RefereeAlias",
    "RefereeSeasonStats",
    "RefereeTeamHistory",
    "RefreshLog",
    "Season",
    "Sport",
    "Team",
    "TeamSquad",
    "User",
    "UserWatchlistFixture",
]
