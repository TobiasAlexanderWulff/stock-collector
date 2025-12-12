import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

def _sqlite_url_from_path(db_path: str) -> str:
    # SQLAlchemy needs 4 slashes for absolute paths: sqlite:////abs/path.db
    p = Path(db_path)
    if p.is_absolute():
        return f"sqlite:////{p.as_posix().lstrip('/')}"
    return f"sqlite:///{p.as_posix()}"

DB_PATH = os.getenv("DB_PATH", "data/stocks.db")

# Ensure parent dir exists (important for Docker volume /data)
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = _sqlite_url_from_path(DB_PATH)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite with FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
