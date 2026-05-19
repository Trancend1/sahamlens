"""Orchestrate formulas → flatten into IndicatorPoint list. No DB."""

from __future__ import annotations

import math
from datetime import date

import pandas as pd
from packages.core.indicators.formulas import macd, rsi_wilder, sma
from packages.core.schemas.models import IndicatorPoint

MA_PERIODS: tuple[int, ...] = (5, 10, 15, 50, 200)
VOLUME_PERIOD = 20
RSI_PERIOD = 14

INDICATOR_KEYS: tuple[str, ...] = (
    *(f"ma_{p}" for p in MA_PERIODS),
    f"vol_avg_{VOLUME_PERIOD}",
    f"rsi_{RSI_PERIOD}",
    "macd_line",
    "macd_signal",
    "macd_hist",
)


def compute_all(symbol: str, prices: pd.DataFrame) -> list[IndicatorPoint]:
    """Compute all MVP indicators for a single symbol, return flat list of points."""
    _validate(prices)

    close = prices["close"].astype("float64")
    volume = prices["volume"].astype("float64")

    series_by_key: dict[str, pd.Series] = {}
    for period in MA_PERIODS:
        series_by_key[f"ma_{period}"] = sma(close, window=period)
    series_by_key[f"vol_avg_{VOLUME_PERIOD}"] = sma(volume, window=VOLUME_PERIOD)
    series_by_key[f"rsi_{RSI_PERIOD}"] = rsi_wilder(close, period=RSI_PERIOD)
    macd_out = macd(close)
    series_by_key["macd_line"] = macd_out["line"]
    series_by_key["macd_signal"] = macd_out["signal"]
    series_by_key["macd_hist"] = macd_out["hist"]

    points: list[IndicatorPoint] = []
    for key, series in series_by_key.items():
        for idx, value in series.items():
            if value is None or (isinstance(value, float) and math.isnan(value)):
                continue
            points.append(
                IndicatorPoint(
                    symbol=symbol,
                    date=_to_date(idx),
                    indicator=key,
                    value=float(value),
                )
            )
    return points


def _validate(prices: pd.DataFrame) -> None:
    if prices.empty:
        raise ValueError("prices DataFrame is empty")
    missing = {"close", "volume"} - set(prices.columns)
    if missing:
        raise ValueError(f"prices missing required columns: {sorted(missing)}")
    if not prices.index.is_monotonic_increasing:
        raise ValueError("prices index must be monotonic ascending")


def _to_date(idx: object) -> date:
    ts = idx if isinstance(idx, pd.Timestamp) else pd.Timestamp(idx)
    result: date = ts.date()
    return result
