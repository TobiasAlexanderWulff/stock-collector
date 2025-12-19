import importlib
import os
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _make_client(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test.db")

    for module_name in ("app.db", "app.models", "app.services.collector", "app.main"):
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def test_collector_status_toggles_with_mocked_ingest(monkeypatch, tmp_path):
    with _make_client(tmp_path) as client:
        from app.db import SessionLocal
        from app.models import Symbol
        from app.services.collector import COLLECTOR

        r = client.post("/api/symbols", json={"symbol": "AAPL"})
        assert r.status_code == 201

        calls = {"count": 0}

        def fake_ingest(db, symbol, interval, now=None):
            calls["count"] += 1
            return 0

        monkeypatch.setattr("app.services.collector.ingest_symbol_interval", fake_ingest)
        COLLECTOR._poll_interval_seconds = 0.01

        r = client.get("/api/collector/status")
        assert r.status_code == 200
        status_payload = r.json()
        assert isinstance(status_payload, list)
        assert len(status_payload) == 1
        assert status_payload[0]["symbol"] == "AAPL"
        assert status_payload[0]["last_attempt_at_utc"] is None
        assert status_payload[0]["last_success_at_utc"] is None
        assert status_payload[0]["last_error"] is None
        assert status_payload[0]["consecutive_failures"] == 0
        assert status_payload[0]["updated_at_utc"] is not None

        r = client.post("/api/collector/start")
        assert r.status_code == 200
        assert r.json()["is_running"] is True

        time.sleep(0.05)

        assert calls["count"] > 0

        r = client.post("/api/collector/stop")
        assert r.status_code == 200
        assert r.json()["is_running"] is False
