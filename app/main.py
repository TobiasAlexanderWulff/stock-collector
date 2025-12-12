from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
import app.models  # noqa: F401
from app.models import Symbol

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_symbols_columns()
    yield


app = FastAPI(lifespan=lifespan)


class SymbolCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    exchange: str | None = Field(default=None, max_length=64)
    timezone: str | None = Field(default=None, max_length=64)


class SymbolRead(BaseModel):
    id: int
    symbol: str
    exchange: str | None
    timezone: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


def _ensure_symbols_columns() -> None:
    with engine.begin() as conn:
        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(symbols)").all()}
        if "exchange" not in cols:
            conn.exec_driver_sql("ALTER TABLE symbols ADD COLUMN exchange VARCHAR(64)")
        if "timezone" not in cols:
            conn.exec_driver_sql("ALTER TABLE symbols ADD COLUMN timezone VARCHAR(64)")
        if "is_active" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE symbols ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"
            )


@app.post("/api/symbols", response_model=SymbolRead, status_code=status.HTTP_201_CREATED)
def create_symbol(payload: SymbolCreate, db: Annotated[Session, Depends(get_db)]):
    symbol = Symbol(
        symbol=payload.symbol,
        exchange=payload.exchange,
        timezone=payload.timezone,
        is_active=True,
    )
    db.add(symbol)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="symbol already exists",
        )
    db.refresh(symbol)
    return symbol


@app.get("/api/symbols", response_model=list[SymbolRead])
def list_symbols(db: Annotated[Session, Depends(get_db)]):
    return db.query(Symbol).order_by(Symbol.id.asc()).all()


@app.delete("/api/symbols/{symbol_id}", response_model=SymbolRead)
def delete_symbol(symbol_id: int, db: Annotated[Session, Depends(get_db)]):
    symbol = db.get(Symbol, symbol_id)
    if symbol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    db.delete(symbol)
    db.commit()
    return symbol
