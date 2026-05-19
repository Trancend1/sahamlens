"""Tests for compute_all engine: shape, warm-up skip, symbol canonicalization."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest
from packages.core.indicators.engine import INDICATOR_KEYS, compute_all


def _synthetic_prices(n: int = 250, start: date = date(2024, 1, 1)) -> pd.DataFrame:
    dates = [start + timedelta(days=i) for i in range(n)]
    return pd.DataFrame(
        {
            "close": [100.0 + i * 0.1 for i in range(n)],
            "volume": [1_000_000 + i * 1_000 for i in range(n)],
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )


def test_compute_all_returns_indicator_points() -> None:
    df = _synthetic_prices(250)
    points = compute_all("bbca", df)

    assert len(points) > 0
    sample = points[0]
    assert sample.symbol == "BBCA.JK"
    assert isinstance(sample.value, float)
    assert sample.indicator in INDICATOR_KEYS


def test_compute_all_skips_warmup_nans() -> None:
    df = _synthetic_prices(250)
    points = compute_all("BBCA", df)
    assert all(p.value == p.value for p in points)


def test_compute_all_emits_expected_count_per_indicator() -> None:
    n = 250
    df = _synthetic_prices(n)
    points = compute_all("BBCA", df)
    counts = {key: 0 for key in INDICATOR_KEYS}
    for p in points:
        counts[p.indicator] += 1

    assert counts["ma_5"] == n - 4
    assert counts["ma_10"] == n - 9
    assert counts["ma_15"] == n - 14
    assert counts["ma_50"] == n - 49
    assert counts["ma_200"] == n - 199
    assert counts["vol_avg_20"] == n - 19
    assert counts["rsi_14"] == n - 14
    assert counts["macd_line"] == n - 25
    assert counts["macd_signal"] == n - 33
    assert counts["macd_hist"] == n - 33


def test_compute_all_macd_emits_three_keys() -> None:
    df = _synthetic_prices(60)
    points = compute_all("BBCA", df)
    keys = {p.indicator for p in points}
    assert {"macd_line", "macd_signal", "macd_hist"}.issubset(keys)


def test_compute_all_rejects_empty_frame() -> None:
    df = pd.DataFrame(columns=["close", "volume"], dtype="float64")
    with pytest.raises(ValueError, match="empty"):
        compute_all("BBCA", df)


def test_compute_all_rejects_missing_columns() -> None:
    df = pd.DataFrame({"close": [1.0, 2.0]})
    with pytest.raises(ValueError, match="volume"):
        compute_all("BBCA", df)


def test_compute_all_rejects_non_monotonic_index() -> None:
    df = pd.DataFrame(
        {"close": [1.0, 2.0, 3.0], "volume": [10, 20, 30]},
        index=pd.DatetimeIndex([date(2024, 1, 3), date(2024, 1, 1), date(2024, 1, 2)]),
    )
    with pytest.raises(ValueError, match="monotonic"):
        compute_all("BBCA", df)


def test_compute_all_short_series_returns_partial() -> None:
    df = _synthetic_prices(10)
    points = compute_all("BBCA", df)
    keys_present = {p.indicator for p in points}
    assert "ma_5" in keys_present
    assert "ma_200" not in keys_present


def test_compute_all_dates_are_date_objects() -> None:
    df = _synthetic_prices(50)
    points = compute_all("BBCA", df)
    assert all(isinstance(p.date, date) for p in points)
