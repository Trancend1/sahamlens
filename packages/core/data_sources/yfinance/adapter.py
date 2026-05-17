"""yfinance OHLCV adapter. Always returns FetchResult — never raises through public API."""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from packages.core.data_sources.normalize import normalize_ticker
from packages.core.schemas.models import FetchResult, PriceRow

logger = logging.getLogger(__name__)

SOURCE_NAME = "yfinance"
USER_AGENT = "SahamLens/1.0 (personal use)"
DEFAULT_MIN_INTERVAL_S = 0.5
DEFAULT_BACKOFF_S: tuple[float, ...] = (1.0, 2.0, 4.0, 8.0)


@dataclass(frozen=True)
class _RateLimitState:
    last_call_at: float = 0.0


def _sleep_if_needed(state: _RateLimitState, min_interval: float, now: float) -> _RateLimitState:
    gap = now - state.last_call_at
    if gap < min_interval:
        time.sleep(min_interval - gap)
    return _RateLimitState(last_call_at=time.monotonic())


def _is_rate_limit_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "too many requests" in msg


class YFinanceSource:
    name = SOURCE_NAME

    def __init__(
        self,
        *,
        min_interval_s: float = DEFAULT_MIN_INTERVAL_S,
        backoff_s: tuple[float, ...] = DEFAULT_BACKOFF_S,
        ticker_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self._min_interval_s = min_interval_s
        self._backoff_s = backoff_s
        self._ticker_factory = ticker_factory or self._default_ticker_factory
        self._state = _RateLimitState()

    @staticmethod
    def _default_ticker_factory(symbol: str) -> Any:
        import yfinance as yf

        return yf.Ticker(symbol)

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> FetchResult:
        canonical = normalize_ticker(symbol)
        fetched_at = datetime.now(UTC)
        try:
            df = self._fetch_with_backoff(canonical, start, end)
        except Exception as exc:  # adapter must never raise through public API
            logger.warning("yfinance fetch failed for %s: %s", canonical, exc)
            return FetchResult(
                symbol=canonical,
                source=SOURCE_NAME,
                fetched_at=fetched_at,
                status="failed",
                rows=[],
                error_message=str(exc),
            )

        rows = self._rows_from_dataframe(canonical, df, fetched_at)
        if rows:
            return FetchResult(
                symbol=canonical,
                source=SOURCE_NAME,
                fetched_at=fetched_at,
                status="ok",
                rows=rows,
            )
        return FetchResult(
            symbol=canonical,
            source=SOURCE_NAME,
            fetched_at=fetched_at,
            status="partial",
            rows=[],
            error_message="empty result",
        )

    def _fetch_with_backoff(self, symbol: str, start: date, end: date) -> Any:
        attempts = [0.0, *self._backoff_s]
        last_exc: Exception | None = None
        for delay in attempts:
            if delay:
                time.sleep(delay)
            self._state = _sleep_if_needed(self._state, self._min_interval_s, time.monotonic())
            try:
                ticker = self._ticker_factory(symbol)
                df = ticker.history(start=start, end=end, auto_adjust=False)
            except Exception as exc:
                last_exc = exc
                if _is_rate_limit_error(exc):
                    continue
                raise
            else:
                return df
        assert last_exc is not None
        raise last_exc

    @staticmethod
    def _rows_from_dataframe(symbol: str, df: Any, fetched_at: datetime) -> list[PriceRow]:
        if df is None or getattr(df, "empty", True):
            return []
        rows: list[PriceRow] = []
        for idx, record in df.iterrows():
            market_date = idx.date() if hasattr(idx, "date") else idx
            rows.append(
                PriceRow(
                    symbol=symbol,
                    date=market_date,
                    open=_safe_float(record.get("Open")),
                    high=_safe_float(record.get("High")),
                    low=_safe_float(record.get("Low")),
                    close=_safe_float(record.get("Close")),
                    volume=_safe_int(record.get("Volume")),
                    source=SOURCE_NAME,
                    fetched_at=fetched_at,
                )
            )
        return rows


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _safe_int(value: Any) -> int | None:
    f = _safe_float(value)
    return None if f is None else int(f)
