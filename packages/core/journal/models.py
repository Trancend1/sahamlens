"""Pydantic models for trade journal. Schema mirrors 0001_initial_schema.sql journal table."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from packages.core.data_sources.normalize import normalize_ticker
from pydantic import BaseModel, field_validator

SetupType = Literal["ma_cross", "breakout", "mean_reversion", "support_bounce", "other"]
TradeStatus = Literal["planned", "open", "closed", "skipped"]
EmotionLevel = Literal["calm", "excited", "fearful", "greedy", "uncertain"]
RiskFlag = Literal["green", "amber", "red", "incomplete"]
CritiqueCategory = Literal["thesis", "invalidation", "risk", "catalyst", "emotion", "liquidity"]
CritiqueStatus = Literal["ok", "weak", "missing"]
WeeklyReviewStatus = Literal["completed", "partial", "failed"]
WeeklyFindingType = Literal[
    "behavior_pattern",
    "rule_violation",
    "missing_data",
    "risk_discipline",
    "follow_up",
    "caveat",
]
WeeklyFindingSeverity = Literal["info", "warning", "critical"]


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


class WeeklyReviewFinding(BaseModel):
    finding_id: str
    review_id: str
    finding_type: WeeklyFindingType
    title: str
    detail: str
    severity: WeeklyFindingSeverity
    evidence: list[str]
    caveats: list[str]
    created_at: datetime


class WeeklyReviewRun(BaseModel):
    review_id: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    status: WeeklyReviewStatus = "completed"
    journal_entry_count: int = 0
    reviewed_plan_count: int = 0
    rule_evaluation_count: int = 0
    violation_count: int = 0
    needs_data_count: int = 0
    summary: str
    evidence: list[str]
    caveats: list[str]
    findings: list[WeeklyReviewFinding]
    rule_evaluations: list[Any]
