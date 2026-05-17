"""PriceSource protocol — uniform interface for all OHLCV adapters.

Mirror DATA_SOURCES.md §6 fallback strategy: each adapter returns FetchResult
with explicit status; caller decides escalation (no silent substitution).
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from packages.core.schemas.models import FetchResult


class PriceSource(Protocol):
    name: str

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> FetchResult: ...
