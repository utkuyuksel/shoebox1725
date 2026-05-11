"""Season aggregates — derived tables, refreshed by workers.

These power the match preview screen. Recomputed from fixtures + per-match
stats whenever a finished match is ingested.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FootballTeamSeasonStats(Base):
    __tablename__ = "football_team_season_stats"

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), primary_key=True)
    season_year: Mapped[int] = mapped_column(Integer, primary_key=True)
    played: Mapped[int] = mapped_column(Integer, default=0)

    # Scoring
    goals_for_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    goals_against_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    xg_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Shots
    shots_total_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    shots_on_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Set pieces / discipline
    corners_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fouls_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    offsides_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    yellow_cards_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    red_cards_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    saves_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Home / Away splits
    home_played: Mapped[int] = mapped_column(Integer, default=0)
    home_goals_for_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    home_goals_against_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    home_corners_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    home_yellow_cards_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    away_played: Mapped[int] = mapped_column(Integer, default=0)
    away_goals_for_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    away_goals_against_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    away_corners_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    away_yellow_cards_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # League context
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wins: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    draws: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    losses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Hit-rates (precomputed for speed)
    over_15_hit_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    over_25_hit_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    over_35_hit_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    btts_hit_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    corners_over_85_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    corners_over_105_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    cards_over_35_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    cards_over_45_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Audit
    last_fixture_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class BasketballTeamSeasonStats(Base):
    __tablename__ = "basketball_team_season_stats"

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), primary_key=True)
    season_year: Mapped[int] = mapped_column(Integer, primary_key=True)
    played: Mapped[int] = mapped_column(Integer, default=0)

    points_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    points_allowed_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fg_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    two_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    three_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ft_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    two_made_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    two_att_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    three_made_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    three_att_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ft_made_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ft_att_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    rebounds_off_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    rebounds_def_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    rebounds_total_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    assists_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    steals_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    blocks_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    turnovers_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Home/Away splits
    home_played: Mapped[int] = mapped_column(Integer, default=0)
    home_points_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    home_points_allowed_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    away_played: Mapped[int] = mapped_column(Integer, default=0)
    away_points_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    away_points_allowed_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wins: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    losses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    total_over_2105_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    spread_cover_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    last_fixture_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FootballPlayerSeasonStats(Base):
    __tablename__ = "football_player_season_stats"

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), primary_key=True)
    season_year: Mapped[int] = mapped_column(Integer, primary_key=True)
    appearances: Mapped[int] = mapped_column(Integer, default=0)
    started: Mapped[int] = mapped_column(Integer, default=0)
    minutes_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    goals: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assists: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shots_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    shots_on_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    passes_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    passes_accurate_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    pass_accuracy_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    interceptions_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    tackles_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fouls_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    was_fouled_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    yellow_cards_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    red_cards_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class BasketballPlayerSeasonStats(Base):
    __tablename__ = "basketball_player_season_stats"

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), primary_key=True)
    season_year: Mapped[int] = mapped_column(Integer, primary_key=True)
    appearances: Mapped[int] = mapped_column(Integer, default=0)
    minutes_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    points_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    rebounds_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    assists_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    steals_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    blocks_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    turnovers_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fg_made_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fg_att_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fg_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    two_made_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    two_att_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    two_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    three_made_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    three_att_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    three_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ft_made_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ft_att_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ft_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
