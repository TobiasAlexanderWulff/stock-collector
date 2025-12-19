from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Candle, Symbol
from app.services.intervals import validate_interval
from app.services.yahoo import fetch_candles

logger = logging.getLogger(__name__)


def _interval_step(interval: str) -> timedelta:
    validate_interval(interval)
    return timedelta(hours=1)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _floor_to_hour(dt: datetime) -> datetime:
    dt = _ensure_utc(dt)
    return dt.replace(minute=0, second=0, microsecond=0)


def get_last_ts(db: Session, symbol_id: int, interval: str) -> datetime | None:
    stmt = select(func.max(Candle.ts_utc)).where(
        Candle.symbol_id == symbol_id,
        Candle.interval == interval,
    )
    return db.execute(stmt).scalar_one_or_none()


def ingest_symbol_interval(
    db: Session,
    symbol: Symbol,
    interval: str,
    *,
    now: datetime | None = None,
) -> int:
    """
    Fetch and insert candles for a single (symbol, interval).

    - Determines `start` as `last_ts + interval_step` (or None if no data yet)
    - Uses `end = now` (UTC)
    - Inserts idempotently (unique constraint prevents duplicates)
    - Ignores constraint violations (does not crash)
    """

    step = _interval_step(interval)

    last_ts = get_last_ts(db, symbol.id, interval)
    start = _ensure_utc(last_ts) + step if last_ts is not None else None
    # Yahoo only serves completed 1h candles, so end must be the last full hour.
    end = _floor_to_hour(now or datetime.now(tz=UTC))

    if start is not None and start >= end:
        logger.info(
            "skip fetch: start_utc >= end_utc (symbol=%s interval=%s start=%s end=%s)",
            symbol.symbol,
            interval,
            start,
            end,
        )
        return 0

    rows = fetch_candles(symbol.symbol, interval, start=start, end=end)
    if not rows:
        return 0

    candles = []
    for row in rows:
        ts_utc = _ensure_utc(row["ts_utc"])
        candles.append(
            Candle(
                symbol_id=symbol.id,
                interval=interval,
                ts_utc=ts_utc,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
            )
        )

    db.add_all(candles)
    try:
        db.commit()
        return len(candles)
    except IntegrityError:
        db.rollback()

    inserted = 0
    for candle in candles:
        db.add(candle)
        try:
            db.commit()
            inserted += 1
        except IntegrityError:
            db.rollback()
        except Exception:
            db.rollback()
            logger.exception(
                "failed to insert candle (symbol=%s interval=%s ts_utc=%s)",
                symbol.symbol,
                interval,
                candle.ts_utc,
            )
            return inserted

    return inserted
