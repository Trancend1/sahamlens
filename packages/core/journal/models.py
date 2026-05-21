"""Pydantic models for trade journal. Schema mirrors 0001_initial_schema.sql journal table."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from packages.core.data_sources.normalize import normalize_ticker
from pydantic import BaseModel, field_validator

SetupType = Literal["ma_cross", "breakout", "mean_reversion", "support_bounce", "other"]
TradeStatus = Literal["planned", "open", "closed", "skipped"]
EmotionLevel = Literal["calm", "excited", "fearful", "greedy", "uncertain"]
RiskFlag = Literal["green", "amber", "red", "incomplete"]
CritiqueCategory = Literal["thesis", "invalidation", "risk", "catalyst", "emotion", "liquidity"]
CritiqueStatus = Literal["ok", "weak", "missing"]


class TradePlan(BaseModel):
    id: int
    symbol: str
    setup_type: SetupType
    thesis: str
    entry_plan: str
    stop_level: float
    invalidation: str
    target: str
    position_size_rupiah: int
    max_loss_rupiah: int
    emotion: EmotionLevel | None = None
    status: TradeStatus = "planned"
    result_rupiah: int | None = None
    lesson: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None

    @field_validator("symbol")
    @classmethod
    def _canon(cls, v: str) -> str:
        return normalize_ticker(v)


class CritiqueCheck(BaseModel):
    category: CritiqueCategory
    status: CritiqueStatus
    finding: str
    suggested_question: str


class JournalCritique(BaseModel):
    plan_id: int
    checks: list[CritiqueCheck]
    overall_risk_flag: RiskFlag
    caveats: list[str]
    not_financial_advice: bool = True
