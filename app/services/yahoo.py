from __future__ import annotations

import logging
from datetime import UTC, datetime

import pandas as pd
import yfinance as yf

from app.services.intervals import validate_interval

logger = logging.getLogger(__name__)


def _to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _normalize_ohlcv_frame(df: pd.DataFrame, symbol: str) -> pd.DataFrame | None:
    if isinstance(df.columns, pd.MultiIndex):
        # Reduce MultiIndex to a single ticker column set if possible.
        for level in reversed(range(df.columns.nlevels)):
            if symbol in df.columns.get_level_values(level):
                df = df.xs(symbol, axis=1, level=level)
                break

        if isinstance(df.columns, pd.MultiIndex):
            df = df.copy()
            df.columns = ["_".join(map(str, tup)) for tup in df.columns.to_list()]

    df = df.rename(columns={c: str(c).strip().lower().replace(" ", "_") for c in df.columns})

    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        logger.error(
            "unexpected yfinance columns (symbol=%s): %s",
            symbol,
            list(df.columns),
        )
        return None

    return df[["open", "high", "low", "close", "volume"]]


def fetch_candles(
    symbol: str,
    interval: str,
    start: datetime | None,
    end: datetime | None,
) -> list[dict]:
    """
    Fetch OHLCV candles from Yahoo Finance using `yfinance`.

    Supported intervals:
    - "1h" (mapped to Yahoo "60m")

    Returns a list of dicts with:
    - ts_utc (timezone-aware datetime in UTC)
    - open, high, low, close, volume
    """

    validate_interval(interval)

    yf_interval = "60m"
    start_utc = _to_utc(start)
    end_utc = _to_utc(end)

    try:
        df = yf.download(
            tickers=symbol,
            interval=yf_interval,
            start=start_utc,
            end=end_utc,
            progress=False,
            auto_adjust=False,
            actions=False,
            threads=False,
        )
    except Exception:
        logger.exception(
            "yfinance download failed (symbol=%s interval=%s start=%s end=%s)",
            symbol,
            interval,
            start_utc,
            end_utc,
        )
        return []

    if df is None or df.empty:
        return []

    df = _normalize_ohlcv_frame(df, symbol)
    if df is None or df.empty:
        return []

    # Normalize index timestamps to UTC (yfinance can return exchange-local tz).
    try:
        idx = df.index
        if getattr(idx, "tz", None) is None:
            idx_utc = pd.to_datetime(idx).tz_localize(UTC)
        else:
            idx_utc = pd.to_datetime(idx).tz_convert(UTC)
    except Exception:
        logger.exception("failed to normalize timestamps to UTC (symbol=%s)", symbol)
        return []

    candles: list[dict] = []
    for ts, (_, row) in zip(idx_utc.to_pydatetime(), df.iterrows(), strict=False):
        try:
            o = float(row["open"])
            h = float(row["high"])
            l = float(row["low"])
            c = float(row["close"])
            v = float(row["volume"])
        except Exception:
            logger.exception("bad OHLCV row from yfinance (symbol=%s)", symbol)
            return []

        candles.append(
            {
                "ts_utc": ts.astimezone(UTC),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": v,
            }
        )

    return candles
