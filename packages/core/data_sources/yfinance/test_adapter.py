"""Tests for YFinanceSource. yfinance.Ticker is replaced with a fake factory.

No live network calls.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from packages.core.data_sources.yfinance.adapter import YFinanceSource


def _fake_df() -> pd.DataFrame:
    idx = pd.to_datetime(["2026-05-12", "2026-05-13"])
    return pd.DataFrame(
        {
            "Open": [10000.0, 10100.0],
            "High": [10150.0, 10225.0],
            "Low": [9975.0, 10050.0],
            "Close": [10100.0, 10200.0],
            "Volume": [52_000_000, 48_500_000],
        },
        index=idx,
    )


def _make_source(ticker_obj: Any) -> YFinanceSource:
    factory = MagicMock(return_value=ticker_obj)
    return YFinanceSource(min_interval_s=0.0, backoff_s=(0.0,), ticker_factory=factory)


def test_fetch_ok_returns_normalized_rows() -> None:
    ticker = MagicMock()
    ticker.history.return_value = _fake_df()
    source = _make_source(ticker)

    result = source.fetch_ohlcv("bbca", date(2026, 5, 12), date(2026, 5, 14))

    assert result.symbol == "BBCA.JK"
    assert result.source == "yfinance"
    assert result.status == "ok"
    assert len(result.rows) == 2
    assert result.rows[0].close == 10100.0
    assert result.rows[0].volume == 52_000_000
    assert result.rows[0].symbol == "BBCA.JK"


def test_empty_dataframe_returns_partial() -> None:
    ticker = MagicMock()
    ticker.history.return_value = pd.DataFrame()
    source = _make_source(ticker)

    result = source.fetch_ohlcv("BBCA.JK", date(2026, 5, 12), date(2026, 5, 14))

    assert result.status == "partial"
    assert result.rows == []
    assert result.error_message == "empty result"


def test_non_rate_limit_exception_returns_failed() -> None:
    ticker = MagicMock()
    ticker.history.side_effect = RuntimeError("boom")
    source = _make_source(ticker)

    result = source.fetch_ohlcv("BBCA.JK", date(2026, 5, 12), date(2026, 5, 14))

    assert result.status == "failed"
    assert result.rows == []
    assert result.error_message is not None
    assert "boom" in result.error_message


def test_rate_limit_retries_then_succeeds() -> None:
    ticker = MagicMock()
    ticker.history.side_effect = [RuntimeError("429 too many"), _fake_df()]
    source = _make_source(ticker)

    result = source.fetch_ohlcv("BBCA.JK", date(2026, 5, 12), date(2026, 5, 14))

    assert result.status == "ok"
    assert ticker.history.call_count == 2


def test_rate_limit_exhausted_returns_failed() -> None:
    ticker = MagicMock()
    ticker.history.side_effect = RuntimeError("429 too many")
    source = _make_source(ticker)

    result = source.fetch_ohlcv("BBCA.JK", date(2026, 5, 12), date(2026, 5, 14))

    assert result.status == "failed"
    assert "429" in (result.error_message or "")


def test_invalid_ticker_returns_failed() -> None:
    source = _make_source(MagicMock())

    with pytest.raises(ValueError):
        source.fetch_ohlcv("BAD-TICKER", date(2026, 5, 12), date(2026, 5, 14))


def test_nan_values_become_none() -> None:
    df = pd.DataFrame(
        {
            "Open": [float("nan")],
            "High": [10150.0],
            "Low": [9975.0],
            "Close": [10100.0],
            "Volume": [float("nan")],
        },
        index=pd.to_datetime(["2026-05-12"]),
    )
    ticker = MagicMock()
    ticker.history.return_value = df
    source = _make_source(ticker)

    result = source.fetch_ohlcv("BBCA.JK", date(2026, 5, 12), date(2026, 5, 14))

    assert result.rows[0].open is None
    assert result.rows[0].volume is None
    assert result.rows[0].close == 10100.0
