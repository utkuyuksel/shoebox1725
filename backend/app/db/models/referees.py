"""Referee + per-season + per-team aggregates.

api-sports.io doesn't expose referee IDs — only a name string on each
fixture. So we generate our own IDs here, normalize names on the way in,
and resolve "Halil Umut Meler" → referee_id via the resolver service.

Hakem-takım eşleşmesi (referee_team_history) feeds the v1 "this ref + this
team historically" insight on the match preview screen.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Referee(Base):
    __tablename__ = "referees"

    # We own these IDs — api-sports doesn't give us referee identifiers.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    # Normalized form used for matching: lowercase, diacritic-stripped,
    # whitespace and punctuation collapsed. Resolver hits this column first.
    name_normalized: Mapped[str] = mapped_column(String, unique=True, index=True)
    nationality: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    first_seen_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RefereeAlias(Base):
    """Manual overrides for names that the auto-normalizer can't unify.

    Populate this when a single ref shows up under different strings
    ("F. Brych" / "Felix Brych" / "Brych, Germany"). Lookup is a hot path
    so we keep it unique-indexed on alias_normalized.
    """

    __tablename__ = "referee_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referee_id: Mapped[int] = mapped_column(
        ForeignKey("referees.id", ondelete="CASCADE")
    )
    alias_normalized: Mapped[str] = mapped_column(String, unique=True, index=True)
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index("idx_referee_aliases_ref", "referee_id"),
    )


class RefereeSeasonStats(Base):
    __tablename__ = "referee_season_stats"

    referee_id: Mapped[int] = mapped_column(ForeignKey("referees.id"), primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), primary_key=True)
    season_year: Mapped[int] = mapped_column(Integer, primary_key=True)
    matches: Mapped[int] = mapped_column(Integer, default=0)
    yellow_cards_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    red_cards_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fouls_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    penalties_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    home_win_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RefereeTeamHistory(Base):
    __tablename__ = "referee_team_history"

    referee_id: Mapped[int] = mapped_column(ForeignKey("referees.id"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    matches: Mapped[int] = mapped_column(Integer, default=0)
    yellow_cards_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    red_cards_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fouls_pg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    last_fixture_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
