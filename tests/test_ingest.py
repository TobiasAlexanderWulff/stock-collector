import importlib
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _setup_db(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test.db")

    for module_name in ("app.db", "app.models", "app.services.ingest"):
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

    from app.db import Base, SessionLocal, engine
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_ingest_is_idempotent(monkeypatch, tmp_path):
    db = _setup_db(tmp_path)
    try:
        from app.models import Candle, Symbol
        from app.services import ingest as ingest_module

        sym = Symbol(symbol="AAPL", exchange=None, timezone=None, is_active=True)
        db.add(sym)
        db.commit()
        db.refresh(sym)

        base = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
        returned = [
            {
                "ts_utc": base,
                "open": 1.0,
                "high": 2.0,
                "low": 0.5,
                "close": 1.5,
                "volume": 100.0,
            },
            {
                "ts_utc": base + timedelta(hours=1),
                "open": 1.1,
                "high": 2.1,
                "low": 0.6,
                "close": 1.6,
                "volume": 110.0,
            },
        ]

        calls = []

        def fake_fetch(symbol, interval, start, end):
            calls.append((symbol, interval, start, end))
            return list(returned)

        monkeypatch.setattr(ingest_module, "fetch_candles", fake_fetch)

        inserted_1 = ingest_module.ingest_symbol_interval(
            db, sym, "1h", now=base + timedelta(hours=2)
        )
        assert inserted_1 == 2
        assert db.query(Candle).count() == 2
        assert calls[-1][2] is None  # start

        inserted_2 = ingest_module.ingest_symbol_interval(
            db, sym, "1h", now=base + timedelta(hours=3)
        )
        assert inserted_2 == 0
        assert db.query(Candle).count() == 2
        assert calls[-1][2] == base + timedelta(hours=2)  # last_ts + 1h
    finally:
        db.close()
