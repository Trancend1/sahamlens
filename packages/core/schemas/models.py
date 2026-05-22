"""Pydantic models shared across data core. Single source of truth for in-process shapes.

DB shape lives in `packages/core/schemas/migrations/`. These models map onto rows of
those tables but may carry extra computed fields (e.g. `derivation`, `fetch_status`).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from packages.core.data_sources.normalize import normalize_ticker
from pydantic import BaseModel, Field, field_validator

FetchStatus = Literal["ok", "partial", "failed"]
Derivation = Literal["raw", "calculated", "ai_derived"]


class WatchlistEntry(BaseModel):
    symbol: str
    tag: str | None = None
    note: str | None = None
    added_at: datetime
    fetched_at: datetime | None = None  # latest price fetch per symbol, from price_history JOIN

    @field_validator("symbol")
    @classmethod
    def _canon(cls, v: str) -> str:
        return normalize_ticker(v)


class PriceRow(BaseModel):
    symbol: str
    date: date
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: int | None
    source: str
    fetched_at: datetime

    @field_validator("symbol")
    @classmethod
    def _canon(cls, v: str) -> str:
        return normalize_ticker(v)


class FetchResult(BaseModel):
    symbol: str
    source: str
    fetched_at: datetime
    status: FetchStatus
    rows: list[PriceRow] = Field(default_factory=list)
    error_message: str | None = None

    @field_validator("symbol")
    @classmethod
    def _canon(cls, v: str) -> str:
        return normalize_ticker(v)


class IndicatorPoint(BaseModel):
    symbol: str
    date: date
    indicator: str
    value: float

    @field_validator("symbol")
    @classmethod
    def _canon(cls, v: str) -> str:
        return normalize_ticker(v)
