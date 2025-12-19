from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Symbol(Base):
    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    candles: Mapped[list["Candle"]] = relationship(
        back_populates="symbol",
        cascade="all, delete-orphan",
    )
    collector_status: Mapped["CollectorStatus"] = relationship(
        back_populates="symbol",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Candle(Base):
    """
    `ts_utc` is stored as a timezone-aware UTC datetime (`DateTime(timezone=True)`).

    Note: SQLite does not enforce timezone semantics; callers must normalize all
    timestamps to UTC before inserting.
    """

    __tablename__ = "candles"
    __table_args__ = (UniqueConstraint("symbol_id", "interval", "ts_utc"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id"), nullable=False)
    interval: Mapped[str] = mapped_column(String(3), nullable=False)
    ts_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)

    symbol: Mapped["Symbol"] = relationship(back_populates="candles")


class CollectorStatus(Base):
    __tablename__ = "collector_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol_id: Mapped[int] = mapped_column(
        ForeignKey("symbols.id"),
        nullable=False,
        unique=True,
    )
    last_attempt_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_success_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    symbol: Mapped["Symbol"] = relationship(back_populates="collector_status")
