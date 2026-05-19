"""Pure-math indicator formulas. No DB, no I/O, no logging.

Signature convention: `pd.Series` in, `pd.Series` out (MACD returns dict of 3 series).
Warm-up rows are NaN (caller filters). RSI uses Wilder smoothing (alpha = 1/period
with SMA seed), MACD uses standard span EMA (alpha = 2/(span+1)).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def rsi_wilder(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder RSI. First valid value at index `period` (uses deltas 1..period as seed)."""
    if period < 2:
        raise ValueError(f"period must be >= 2, got {period}")
    delta = close.diff()
    gain = delta.clip(lower=0).fillna(0.0)
    loss = (-delta).clip(lower=0).fillna(0.0)

    result = pd.Series(np.nan, index=close.index, dtype="float64")
    if len(close) <= period:
        return result

    avg_gain = gain.iloc[1 : period + 1].mean()
    avg_loss = loss.iloc[1 : period + 1].mean()
    result.iloc[period] = _rsi_from_avgs(avg_gain, avg_loss)

    for i in range(period + 1, len(close)):
        avg_gain = (avg_gain * (period - 1) + gain.iloc[i]) / period
        avg_loss = (avg_loss * (period - 1) + loss.iloc[i]) / period
        result.iloc[i] = _rsi_from_avgs(avg_gain, avg_loss)

    return result


def _rsi_from_avgs(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0 and avg_gain == 0:
        return float("nan")
    if avg_loss == 0:
        return 100.0
    if avg_gain == 0:
        return 0.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, pd.Series]:
    """Standard MACD: line = EMA(fast) - EMA(slow), signal = EMA(line, signal), hist = line - signal."""
    if not (0 < fast < slow):
        raise ValueError(f"require 0 < fast < slow, got fast={fast} slow={slow}")
    if signal < 1:
        raise ValueError(f"signal must be >= 1, got {signal}")
    line = ema(close, span=fast) - ema(close, span=slow)
    signal_line = ema(line.dropna(), span=signal).reindex(close.index)
    hist = line - signal_line
    return {"line": line, "signal": signal_line, "hist": hist}
