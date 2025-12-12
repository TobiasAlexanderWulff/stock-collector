# Worldwide Stock Candle Collector

A minimal, research-focused system that continuously collects **global OHLCV candle data**
from Yahoo Finance and exposes collector status and data gaps via a lightweight web interface.

Built as a **research tool**, **portfolio project**, and **technical foundation** for
time-series analysis (TSA) and ML/AI experiments.

---

## Key Features

- **Global market support** (US, EU, Asia – symbol based)
- **Multiple time resolutions**: `1d` (daily) and `1h` (intraday)
- **Idempotent data ingestion** (no duplicate candles)
- **Minimal web dashboard** (status, symbols)
- **Dockerized setup** for reproducibility and easy deployment

---

## Preview

![Web Interface Screenshot](docs/screenshots/screenshot_webinterface.png)

---

## Architecture (High Level)

```text
           +-------------------+
           |   Web Dashboard   |
           | (FastAPI + HTML)  |
           +---------+---------+
                     |
                     v
           +-------------------+
           |   Collector Loop  |
           |  (Background Task)|
           +---------+---------+
                     |
                     v
           +-------------------+
           | Yahoo Finance API |
           |   (yfinance)     |
           +---------+---------+
                     |
                     v
           +-------------------+
           |   SQLite Database |
           | (SQLAlchemy ORM)  |
           +-------------------+
```

Detailed explanation: [docs/architecture.md](docs/architecture.md)

---

## Quickstart

*Option A - Local (Python venv)*

```bash
git clone https://github.com/tobiasalexanderwulff/stock-collector
cd stock-collector

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
# optional: override DB location (default: data/stocks.db)
# export DB_PATH=data/stocks.db
uvicorn app.main:app --reload
```

Open: [http://localhost:8000](http://localhost:8000)

---

*Option B - Docker (Recommended)*

```bash
docker compose -f docker/docker-compose.yml up --build
```

- App: [http://localhost:8000](http://localhost:8000)
- Data persisted on host at `./data/stocks.db` (volume-mounted into container as `/data/stocks.db`)

---

## DB_PATH

The SQLite database path is configured via `DB_PATH`:

- Default (local): `data/stocks.db`
- Docker: `DB_PATH=/data/stocks.db` (see `docker/docker-compose.yml`)

---

## Example Workflow

1. Add symbols (e.g. `AAPL`, `^N225`, `RELIANCE.NS`)
2. Start collector
3. Candles are fetched periodically (`1d`, `1h`)
4. Inspect collector status in the UI

---

## Minimal API Usage (curl)

Create symbol:

```bash
curl -sS -X POST http://localhost:8000/api/symbols \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"AAPL","exchange":"NASDAQ","timezone":"America/New_York"}'
```

List symbols:

```bash
curl -sS http://localhost:8000/api/symbols
```

Delete symbol:

```bash
curl -sS -X DELETE http://localhost:8000/api/symbols/1
```

Start collector:

```bash
curl -sS -X POST http://localhost:8000/api/collector/start
```

Collector status:

```bash
curl -sS http://localhost:8000/api/collector/status
```

Stop collector:

```bash
curl -sS -X POST http://localhost:8000/api/collector/stop
```

---

## Data Model (MVP)

*Symbol*

- `id`
- `symbol`
- `exchange`
- `timezone`
- `is_active`

*Candle*

- `symbol_id`
- `interval`
- `ts_utc`
- `open, high, low, close, volume`

Unique constraint:

```scss
(symbol_id, interval, ts_utc)
```

---

## Design Decisions

*Why `1d` + `1h`?* 

- `1d`: stable long-term history for TSA (ARIMA, GARCH, regime models)
- `1h`: intraday structure without 1-minute data chaos or provider limits

*Why SQLAlchemy + SQLite?*

- Clean ORM models
- Idempotent inserts via constraints
- Easy migration path to Postgres / TimescaleDB

*Why UTC everywhere?*

- Avoid cross-market timezone bugs
- Essential for global time-series alignment

*Why Docker?*

- Reproducibility
- Clean deployment story

---

## Known Limitations

- Yahoo Finance intraday data is *not infinite historical backfill*
- Market holidays and session breaks are not calendar-aware (yet)
- Not intended for trading or execution

These are documented and deliberate MVP trade-offs.

---

## Roadmap

- Exchange-aware trading calendars
- Postgres / TimescaleDB backend
- Provider abstractions (Polyfon, Alpaca, etc.)
- Export pipelines fot TSA / ML workflows
- VPS deployment

---

## Context

This project was built as part of my *Bachelor thesis preparation* and serves as reusable resarch asset for:

- Time-series analysis
- Market regime modeling
- ML/AI experiments on financial data

-- Author

*Tobias Alexander Wulff*
Computer Visualization & Design (B.Sc.)
Interest areas: AI, ML systems, data enginieering, research tooling

- LinkedIn: [https://linkedin.com/in/tobias-wulff-2235253a0/](https://linkedin.com/in/tobias-wulff-2235253a0/)
- GitHub: [https://github.com/tobiasalexanderwulff/](https://github.com/tobiasalexanderwulff/)

---

## License

This project is licensed under the [MIT License](LICENSE).
