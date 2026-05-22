"""Pydantic model for portfolio_position table row."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from packages.core.data_sources.normalize import normalize_ticker
from pydantic import BaseModel, field_validator

PositionSource = Literal["csv", "manual"]


class PortfolioPosition(BaseModel):
    symbol: str
    lots: int
    avg_price: float
    imported_at: datetime
    source: PositionSource

    @field_validator("symbol")
    @classmethod
    def _canon(cls, v: str) -> str:
        return normalize_ticker(v)
