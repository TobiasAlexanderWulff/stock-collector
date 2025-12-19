from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.db import SessionLocal
from sqlalchemy.orm import Session

from app.models import CollectorStatus, Symbol
from app.services.ingest import ingest_symbol_interval
from app.services.intervals import ALLOWED_INTERVALS, validate_interval

logger = logging.getLogger(__name__)
_MAX_ERROR_LEN = 500


def _get_or_create_status(db: Session, symbol_id: int) -> CollectorStatus:
    status = (
        db.query(CollectorStatus)
        .filter(CollectorStatus.symbol_id == symbol_id)
        .one_or_none()
    )
    if status is not None:
        return status

    status = CollectorStatus(symbol_id=symbol_id)
    db.add(status)
    db.flush()
    return status


def _truncate_error(message: str) -> str:
    if len(message) <= _MAX_ERROR_LEN:
        return message
    return message[:_MAX_ERROR_LEN]


def _interval_step(interval: str) -> timedelta:
    validate_interval(interval)
    return timedelta(hours=1)


@dataclass
class CollectorState:
    is_running: bool = False
    last_run: datetime | None = None
    last_error: str | None = None


class Collector:
    def __init__(self, *, poll_interval_seconds: float = 2.0):
        self.state = CollectorState()
        self._poll_interval_seconds = poll_interval_seconds
        self._lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._next_run: dict[tuple[int, str], datetime] = {}

    def status(self) -> CollectorState:
        return self.state

    async def start(self) -> None:
        async with self._lock:
            if self._task is not None and not self._task.done():
                return
            self._stop_event.clear()
            self.state.is_running = True
            self.state.last_error = None
            self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        async with self._lock:
            self._stop_event.set()
            task = self._task
            self._task = None

        if task is None:
            self.state.is_running = False
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self.state.is_running = False

    async def _run_loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                await self._tick()
                await asyncio.sleep(self._poll_interval_seconds)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.state.last_error = str(e)
            logger.exception("collector loop crashed")
        finally:
            self.state.is_running = False

    async def _tick(self) -> None:
        now = datetime.now(tz=UTC)
        self.state.last_run = now

        db = SessionLocal()
        try:
            symbols = (
                db.query(Symbol)
                .filter(Symbol.is_active.is_(True))
                .order_by(Symbol.id.asc())
                .all()
            )
            active_ids = {s.id for s in symbols}
            for key in list(self._next_run.keys()):
                if key[0] not in active_ids:
                    self._next_run.pop(key, None)

            for symbol in symbols:
                for interval in ALLOWED_INTERVALS:
                    key = (symbol.id, interval)
                    due_at = self._next_run.get(key)
                    if due_at is not None and due_at > now:
                        continue

                    attempt_time = datetime.now(tz=UTC)
                    status = _get_or_create_status(db, symbol.id)
                    status.last_attempt_at_utc = attempt_time
                    status.updated_at_utc = attempt_time
                    db.commit()

                    try:
                        ingest_symbol_interval(db, symbol, interval, now=now)
                    except Exception as e:
                        db.rollback()
                        error_time = datetime.now(tz=UTC)
                        status = _get_or_create_status(db, symbol.id)
                        status.last_error = _truncate_error(str(e))
                        status.consecutive_failures = (
                            status.consecutive_failures or 0
                        ) + 1
                        status.updated_at_utc = error_time
                        db.commit()
                        self.state.last_error = str(e)
                        logger.exception(
                            "collector ingest failed (symbol=%s interval=%s)",
                            symbol.symbol,
                            interval,
                        )
                    else:
                        success_time = datetime.now(tz=UTC)
                        status.last_success_at_utc = success_time
                        status.last_error = None
                        status.consecutive_failures = 0
                        status.updated_at_utc = success_time
                        db.commit()
                    finally:
                        self._next_run[key] = now + _interval_step(interval)
        finally:
            db.close()


COLLECTOR = Collector()
