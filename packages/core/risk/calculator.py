"""Position size calculator for IDX equities.

Formula (ARCHITECTURE.md §7):
  risk_rupiah  = portfolio_value * risk_percent
  risk_per_lot = (entry_price - stop_price) * 100   [1 lot = 100 shares on IDX]
  max_lots     = floor(risk_rupiah / risk_per_lot)
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionSizeResult:
    lots: int
    position_size_rupiah: int
    max_loss_rupiah: int
    risk_rupiah: int


def position_size(
    portfolio_value: int,
    risk_percent: float,
    entry_price: float,
    stop_price: float,
) -> PositionSizeResult:
    """Compute max position size given a portfolio risk budget and stop distance.

    Returns lots=0 when stop_price >= entry_price or risk_percent <= 0.
    """
    risk_rupiah = int(portfolio_value * risk_percent)
    if risk_percent <= 0 or stop_price >= entry_price or entry_price <= 0:
        return PositionSizeResult(
            lots=0,
            position_size_rupiah=0,
            max_loss_rupiah=0,
            risk_rupiah=risk_rupiah,
        )
    price_diff = entry_price - stop_price
    risk_per_lot = price_diff * 100
    max_lots = math.floor(risk_rupiah / risk_per_lot)
    return PositionSizeResult(
        lots=max_lots,
        position_size_rupiah=int(max_lots * entry_price * 100),
        max_loss_rupiah=int(max_lots * risk_per_lot),
        risk_rupiah=risk_rupiah,
    )
