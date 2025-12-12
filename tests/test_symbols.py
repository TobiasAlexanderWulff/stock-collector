import importlib
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _make_client(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DB_PATH"] = str(db_path)

    for module_name in ("app.db", "app.models", "app.main"):
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def test_add_list_delete_and_duplicate_rejection(tmp_path):
    with _make_client(tmp_path) as client:
        r = client.post("/api/symbols", json={"symbol": "AAPL"})
        assert r.status_code == 201
        created = r.json()
        assert created["symbol"] == "AAPL"
        assert created["is_active"] is True

        r = client.get("/api/symbols")
        assert r.status_code == 200
        symbols = r.json()
        assert len(symbols) == 1
        assert symbols[0]["symbol"] == "AAPL"

        r = client.post("/api/symbols", json={"symbol": "AAPL"})
        assert r.status_code in (400, 409)

        symbol_id = created["id"]
        r = client.delete(f"/api/symbols/{symbol_id}")
        assert r.status_code == 200

        r = client.get("/api/symbols")
        assert r.status_code == 200
        assert r.json() == []
