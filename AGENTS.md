# AGENTS.md — Codex Instructions

## Project

**Name:** Worldwide Stock Candle Collector
**Type:** Research / Portfolio / Bachelor-prep project
**Primary goal:** Build a minimal, reliable system that continuously collects OHLCV candles worldwide and exposes status & gaps via a simple web UI.

This is an MVP. Stability, clarity, and documentation matter more than features.

---

## Hard Constraints (Non-Negotiable)

- **No authentication, no users, no accounts**
- **No React / SPA frameworks**
- **No feature creep**
- **Only one data provider:** Yahoo Finance via `yfinance`
- **Only one interval:** `1h` (`60m`)
- **Database:** SQLite **only** (SQLAlchemy ORM)
- **No Alembic migrations** in MVP
- **All timestamps stored in UTC**
- **Idempotent inserts only** (no duplicates, enforced by DB constraints)

If a feature is not listed here or in `PLANS.md`, it must NOT be implemented.

---

## Tech Stack (Fixed)

- Python 3.12
- FastAPI
- SQLAlchemy ORM
- SQLite
- yfinance
- Jinja2 (or plain HTML templates)
- Docker + docker-compose
- pytest (basic tests only)

---

## Repository Structure (Expected)

```text
.
├── AGENTS.md
├── app
│   ├── db.py
│   ├── main.py
│   ├── models.py
│   ├── services
│   │   ├── collector.py
│   │   ├── gaps.py
│   │   ├── intervals.py
│   │   └── yahoo.py
│   └── web
│       ├── static
│       │   ├── app.css
│       │   └── app.js
│       └── templates
│           └── index.html
├── CHANGELOG.md
├── data
├── docker
│   ├── docker-compose.yml
│   └── Dockerfile
├── docs
│   ├── archticture.md
│   └── screenshots
├── LICENSE
├── PLANS.md
├── README.md
├── requirements.txt
└── tests
    ├── test_db.py
    ├── test_gaps.py
    └── test_yahoo_integration.py
```

Do NOT introduce additional layers or folders unless strictly necessary.

---

## Database Rules

- Use SQLAlchemy ORM models
- Create tables automatically on startup(`Base.metadata.create_all`)
- Candle table must have a **unique constraint** on:
  `(symbol_id, interval, ts_utc)`
- Database file must live at `/data/stocks.db` (mounted volume in Docker)

---

## Collector Rules

- Collector must be startable/stoppable via API or UI
- Use a background task / loop (no external schedulers)
- Fetch:
  - `1h`: once per hour per symbol
- Determine fetch start as:
  `last_stored_ts + interval`
- Never overwrite existing candles
- Handle empty or throttled responses gracefully

---

## Gap Detection

- Gaps are defined as missing expected timestamps
- Do NOT attempt advanced calendar locig in MVP
- Report gaps honestly (do not fabricate candles)

---

## Docker Requirements

- Docker build must succeed
- `docker compose up` must start the app
- SQLite DB must persist via volume mount
- No multi-container setup in MVP

---

## Documentation

Every completed milestone MUST update documentation.

Required docs:
- `README.md`
  - Project overview
  - Quickstart (local + Docker)
  - Design decisions
- `docs/architecture.md`
  - High-level system diagram
- At least **2 screenshots** in `docs/screenshots/`

Documentation is part of the deliverable, not optional.

---

## Defintion of Done (MVP)

The project is considered DONE when:

- Symbols can be added and listed
- Collector can be started and stopped
- Candles for `1h` are persisted without duplicates
- A basic gap report is visible
- Docker setup works out-of-the-box
- README and architecture docs are complete

---

## Agent Behavior

- Prefer simple, explicit code over abstractions
- Ask for clarification ONLY if requirements are ambiguous
- Do not refactor working code without explicit instruction
- Optimize for correctness and readablility, not cleverness

This project is evaluated as a **research tool and portfolio artifact**.
Build accordingly.
