"""Fixture (match) + per-match per-team stats.

Per-match stats are required to compute hit-rates (e.g. Over 2.5 %, BTTS %),
trend graphs (last 10 match line vs season average), and referee-team
aggregates. They are the canonical input for everything downstream.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Fixture(Base):
    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    season_year: Mapped[int] = mapped_column(Integer)
    round: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    kickoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String)
    is_finished: Mapped[bool] = mapped_column(
        Boolean,
        Computed("status IN ('FT', 'AET', 'PEN')", persisted=True),
    )
    home_goals: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    home_goals_ht: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_goals_ht: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    referee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("referees.id"), nullable=True)
    venue: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_fixtures_league_season", "league_id", "season_year"),
        Index("idx_fixtures_kickoff", "kickoff_at"),
        Index("idx_fixtures_team_kickoff", "home_team_id", "kickoff_at"),
        Index("idx_fixtures_away_team", "away_team_id", "kickoff_at"),
        Index("idx_fixtures_referee", "referee_id", "kickoff_at"),
    )


class FootballFixtureTeamStats(Base):
    __tablename__ = "football_fixture_team_stats"

    fixture_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fixtures.id", ondelete="CASCADE"), primary_key=True
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    is_home: Mapped[bool] = mapped_column(Boolean)
    shots_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shots_on: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shots_off: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shots_blocked: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shots_inside_box: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shots_outside_box: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fouls: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    corners: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    offsides: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    possession_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    yellow_cards: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    red_cards: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    saves: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passes_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passes_accurate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pass_accuracy_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    xg: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)

    __table_args__ = (
        Index("idx_ffts_team", "team_id"),
    )


class BasketballFixtureTeamStats(Base):
    __tablename__ = "basketball_fixture_team_stats"

    fixture_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fixtures.id", ondelete="CASCADE"), primary_key=True
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    is_home: Mapped[bool] = mapped_column(Boolean)
    points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    field_goals_made: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    field_goals_att: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    two_points_made: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    two_points_att: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    three_points_made: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    three_points_att: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    free_throws_made: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    free_throws_att: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rebounds_offensive: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rebounds_defensive: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assists: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    steals: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    blocks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    turnovers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fouls: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_bfts_team", "team_id"),
    )
