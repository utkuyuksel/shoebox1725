"""Sport / League / Season — the catalog of what we cover."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Sport(Base):
    __tablename__ = "sports"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sport_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("sports.id"))
    name: Mapped[str] = mapped_column(String)
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=999)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    is_free_tier: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    seasons: Mapped[list["Season"]] = relationship(back_populates="league", cascade="all,delete-orphan")

    __table_args__ = (
        Index("idx_leagues_sport_active", "sport_id", "is_active"),
        Index("idx_leagues_country_sort", "country", "sort_order"),
    )


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"))
    year: Mapped[int] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    current_round: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    league: Mapped[League] = relationship(back_populates="seasons")

    __table_args__ = (
        UniqueConstraint("league_id", "year", name="uniq_seasons_league_year"),
    )
