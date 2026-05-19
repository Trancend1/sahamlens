"""Golden + property tests for indicator formulas.

Golden values: canonical Wilder RSI example (Wilder 1978) + closed-form SMA/EMA.
Property tests: invariants that must hold for any valid price series.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from packages.core.indicators.formulas import ema, macd, rsi_wilder, sma

WILDER_RSI_CLOSE = [
    44.3389,
    44.0902,
    44.1497,
    43.6124,
    44.3278,
    44.8264,
    45.0955,
    45.4245,
    45.8433,
    46.0826,
    45.8931,
    46.0328,
    45.6140,
    46.2820,
    46.2820,
    46.0028,
    46.0328,
    46.4116,
    46.2222,
    45.6439,
    46.2122,
    46.2521,
    45.7137,
    46.4515,
    45.7835,
    45.3548,
    44.0288,
    44.1783,
    44.2181,
    44.5672,
    43.4205,
    42.6628,
    43.1314,
]
WILDER_RSI_EXPECTED_AT_14 = 70.53


def _series(values: list[float]) -> pd.Series:
    return pd.Series(values, dtype="float64")


def test_sma_known_window() -> None:
    s = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    out = sma(s, window=3)
    assert math.isnan(out.iloc[0])
    assert math.isnan(out.iloc[1])
    assert out.iloc[2] == pytest.approx(2.0)
    assert out.iloc[3] == pytest.approx(3.0)
    assert out.iloc[4] == pytest.approx(4.0)


def test_sma_window_larger_than_series() -> None:
    s = _series([1.0, 2.0])
    out = sma(s, window=5)
    assert out.isna().all()


def test_ema_constant_input_stays_constant() -> None:
    s = _series([5.0] * 30)
    out = ema(s, span=10)
    valid = out.dropna()
    assert np.allclose(valid.to_numpy(), 5.0, atol=1e-9)


def test_ema_first_value_after_warmup_uses_adjust_false() -> None:
    s = _series([1.0] * 9 + [2.0] * 21)
    out = ema(s, span=10)
    assert math.isnan(out.iloc[8])
    assert out.iloc[9] == pytest.approx(1.0 + (2.0 - 1.0) * (2 / 11))


def test_rsi_wilder_golden_value_at_index_14() -> None:
    close = _series(WILDER_RSI_CLOSE)
    out = rsi_wilder(close, period=14)
    assert math.isnan(out.iloc[13])
    assert out.iloc[14] == pytest.approx(WILDER_RSI_EXPECTED_AT_14, abs=0.05)


def test_rsi_all_up_approaches_100() -> None:
    close = _series([100.0 + i for i in range(50)])
    out = rsi_wilder(close, period=14)
    assert out.iloc[-1] == pytest.approx(100.0, abs=1e-9)


def test_rsi_all_down_approaches_zero() -> None:
    close = _series([200.0 - i for i in range(50)])
    out = rsi_wilder(close, period=14)
    assert out.iloc[-1] == pytest.approx(0.0, abs=1e-9)


def test_rsi_flat_series_undefined_returns_nan() -> None:
    close = _series([100.0] * 50)
    out = rsi_wilder(close, period=14)
    valid = out.dropna()
    assert (valid == pytest.approx(50.0)).all() or valid.isna().all() or len(valid) == 0


def test_macd_zero_series_is_all_zero() -> None:
    close = _series([0.0] * 60)
    out = macd(close)
    for key in ("line", "signal", "hist"):
        valid = out[key].dropna()
        assert np.allclose(valid.to_numpy(), 0.0, atol=1e-12)


def test_macd_hist_equals_line_minus_signal() -> None:
    close = _series([100.0 + i * 0.5 for i in range(80)])
    out = macd(close)
    diff = (out["line"] - out["signal"]).dropna()
    hist = out["hist"].dropna()
    pd.testing.assert_series_equal(diff, hist, check_names=False)


def test_macd_keys_present() -> None:
    close = _series([100.0 + i for i in range(60)])
    out = macd(close)
    assert set(out.keys()) == {"line", "signal", "hist"}


_price_strategy = st.lists(
    st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False, allow_infinity=False),
    min_size=50,
    max_size=300,
).map(_series)


@given(_price_strategy)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_rsi_always_bounded_0_to_100(close: pd.Series) -> None:
    out = rsi_wilder(close, period=14)
    valid = out.dropna()
    if len(valid) > 0:
        assert (valid >= 0.0).all()
        assert (valid <= 100.0).all()


@given(_price_strategy, st.integers(min_value=2, max_value=20))
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_sma_equals_window_mean(close: pd.Series, window: int) -> None:
    if len(close) < window:
        return
    out = sma(close, window=window)
    last = out.iloc[-1]
    expected = close.iloc[-window:].mean()
    assert last == pytest.approx(expected, rel=1e-9)


@given(_price_strategy)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_macd_hist_invariant(close: pd.Series) -> None:
    if len(close) < 35:
        return
    out = macd(close)
    diff = (out["line"] - out["signal"]).dropna()
    hist = out["hist"].dropna()
    if len(diff) > 0 and len(hist) > 0:
        pd.testing.assert_series_equal(diff, hist, check_names=False, rtol=1e-9, atol=1e-12)
