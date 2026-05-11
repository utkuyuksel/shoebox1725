"""Operational tables — refresh log for QStash worker visibility."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RefreshLog(Base):
    __tablename__ = "refresh_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_kind: Mapped[str] = mapped_column(String)
    entity_id: Mapped[str] = mapped_column(String)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String, default="running")
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    api_calls: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        Index("idx_refresh_log_entity", "entity_kind", "entity_id", "finished_at"),
        Index("idx_refresh_log_status", "status", "started_at"),
    )
