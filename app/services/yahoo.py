from __future__ import annotations

import logging
from datetime import UTC, datetime

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def _to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def fetch_candles(
    symbol: str,
    interval: str,
    start: datetime | None,
    end: datetime | None,
) -> list[dict]:
    """
    Fetch OHLCV candles from Yahoo Finance using `yfinance`.

    Supported intervals:
    - "1d" (daily)
    - "1h" (mapped to Yahoo "60m")

    Returns a list of dicts with:
    - ts_utc (timezone-aware datetime in UTC)
    - open, high, low, close, volume
    """

    if interval not in ("1d", "1h"):
        raise ValueError("Only intervals '1d' and '1h' are supported")

    yf_interval = "1d" if interval == "1d" else "60m"
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
    for ts, row in zip(idx_utc.to_pydatetime(), df.itertuples(index=False), strict=False):
        # DataFrame may have "Open/High/Low/Close/Volume" columns.
        row_dict = getattr(row, "_asdict", None)
        if callable(row_dict):
            values = row._asdict()
        else:
            # Fallback for older pandas / unexpected tuple structure.
            values = dict(zip(df.columns, row, strict=False))

        try:
            o = float(values["Open"])
            h = float(values["High"])
            l = float(values["Low"])
            c = float(values["Close"])
            v = float(values.get("Volume", 0.0))
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
