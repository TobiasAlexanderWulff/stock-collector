import os
from datetime import UTC, datetime, timedelta

import pytest

from app.services.yahoo import fetch_candles


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_YAHOO_INTEGRATION") != "1",
    reason="set RUN_YAHOO_INTEGRATION=1 to run (requires network access)",
)
def test_fetch_candles_returns_ohlcv_with_utc_timestamps():
    end = datetime.now(tz=UTC)
    start = end - timedelta(days=7)

    candles = fetch_candles("AAPL", "1d", start=start, end=end)
    assert isinstance(candles, list)
    assert len(candles) > 0

    c0 = candles[0]
    assert set(c0.keys()) == {"ts_utc", "open", "high", "low", "close", "volume"}
    assert c0["ts_utc"].tzinfo is not None
    assert c0["ts_utc"].utcoffset() == timedelta(0)
