"""Aggregate-only portfolio exposure for the agentic layer (ADR-0019 D5).

Hard privacy boundary: lot size, average price, and absolute rupiah value MUST
NOT appear in any output. Only dimensionless relative weights and counts are
exposed, so the summary is safe to send to an LLM or chat surface. Weights are
ratios of value, rounded to one decimal, and cannot be reversed into the
underlying lots or prices.
"""

from __future__ import annotations

import duckdb
from packages.core.portfolio.repo import list_positions
from pydantic import BaseModel

AGGREGATE_ONLY_NOTE = (
    "Aggregate exposure only. Lot size, average price, and profit/loss detail "
    "are intentionally excluded."
)


class ExposureHolding(BaseModel):
    """A single holding expressed only as a relative value weight (percent)."""

    symbol: str
    weight_pct: float


class ExposureSummary(BaseModel):
    """Portfolio concentration without any absolute lot, price, or rupiah value."""

    position_count: int
    holdings: list[ExposureHolding]
    top_concentration_pct: float
    top3_concentration_pct: float
    note: str = AGGREGATE_ONLY_NOTE
    not_financial_advice: bool = True


def exposure_summary(conn: duckdb.DuckDBPyConnection) -> ExposureSummary:
    """Return aggregate-only exposure. Reads `portfolio_position`, writes nothing."""
    positions = list_positions(conn)
    if not positions:
        return ExposureSummary(
            position_count=0,
            holdings=[],
            top_concentration_pct=0.0,
            top3_concentration_pct=0.0,
        )

    values = [(p.symbol, max(p.lots, 0) * max(p.avg_price, 0.0)) for p in positions]
    total = sum(value for _, value in values)
    if total <= 0:
        return ExposureSummary(
            position_count=len(positions),
            holdings=[ExposureHolding(symbol=symbol, weight_pct=0.0) for symbol, _ in values],
            top_concentration_pct=0.0,
            top3_concentration_pct=0.0,
        )

    holdings = [
        ExposureHolding(symbol=symbol, weight_pct=round(value / total * 100, 1))
        for symbol, value in values
    ]
    holdings.sort(key=lambda h: h.weight_pct, reverse=True)
    return ExposureSummary(
        position_count=len(positions),
        holdings=holdings,
        top_concentration_pct=holdings[0].weight_pct,
        top3_concentration_pct=round(sum(h.weight_pct for h in holdings[:3]), 1),
    )
