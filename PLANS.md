# PLANS.md — Execution Plan (MVP)

## Objective

Build a minimal, production-style MVP that collects worldwide OHLCV candle data
(1d and 1h) from Yahoo Finance and exposes collector status and data gaps via a
simple web interface.

This project serves as:

- Research tooling (TSA / ML experiments)
- A portfolio / LinkedIn showcase
- Technical groundwork for future extensions

---

## Scope (Strict)

- Data provider: Yahoo Finance (`yfinance`)
- Intervals: `1d`, `1h` (60m)
- Markets: Global (symbol-based, no auto-discovery)
- Storage: SQLite via SQLAlchemy ORM
- UI: Minimal server-rendered HTML
- Deployment: Docker (single container)

---

## Non-Scope (Explicit)

- No authentication or users
- No advanced exchange calendars
- No backtesting or trading logic
- No data normalization beyond OHLCV
- No real-time streaming (polling only)
- No multi-container or cloud infrastructure

---

## Milestones

### M1 — Project Skeleton & Persistence

**Deliverables**

- FastAPI app skeleton
- SQLAlchemy models (`Symbol`, `Candle`)
- SQLite DB initialization on startup
- CRUD endpoints for symbols (add/list/remove)

**Acceptance**

- App starts via `uvicorn`
- Adding a symbol persists to DB
- Duplicate symbols are rejected

---

### M2 — Yahoo Provider & Candle Ingestion

**Deliverables**

- `fetch_candles()` using `yfinance`
- Support for `1d` and `1h`
- UTC timestamp normalization
- Idempotent candle insertion

**Acceptance**

- Candles are inserted for at least one symbol
- Re-running ingestion creates no duplicates
- Empty provider responses handled safely

---

### M3 — Collector Loop & Scheduling

**Deliverables**

- Background collector task
- Start/stop control
- Per-symbol, per-interval scheduling
- Status tracking (last run, last error)

**Acceptance**

- Collector can be started and stopped
- Candles accumulate over time
- Errors do not crash the app

---

### M4 — Gap Detection

**Deliverables**

- Simple gap detection logic
- Gap summary per symbol & interval
- Human-readable output

**Acceptance**

- Gaps are detected when timestamps are missing
- No false positives on contiguous data

---

### M5 — Web UI

**Deliverables**

- Minimal dashboard
- Symbol list & add form
- Collector status (running/stopped)
- Gap overview

**Acceptance**

- UI usable without JavaScript frameworks
- All core functions accessible from browser

---

### M6 — Docker & Documentation

**Deliverables**

- Dockerfile
- docker-compose.yml
- README with Quickstart (local + Docker)
- `docs/architecture.md`
- At least 2 screenshots

**Acceptance**

- `docker compose up` starts the app
- Data persists across restarts
- Documentation reflects actual behavior

---

## Risks & Mitigations

- Yahoo intraday limits → treat `1h` as rolling window
- Market closures misdetected as gaps → documented limitation
- Rate limiting → graceful degradation, no crashes

---

## Definition of Done

The MVP is complete when all milestones M1–M6 pass their acceptance criteria
and documentation is up to date.
