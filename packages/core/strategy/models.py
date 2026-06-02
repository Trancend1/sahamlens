"""Simple named strategy-rule models for V1-S4."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

StrategyRuleCategory = Literal[
    "journal_completeness",
    "risk_discipline",
    "plan_adherence",
    "emotion_discipline",
    "review_hygiene",
]
NeedsDataBehavior = Literal["needs_data", "skip"]
StrategyEvaluationStatus = Literal["pass", "fail", "needs_data", "skipped"]


class StrategyRule(BaseModel):
    rule_id: str
    name: str
    description: str
    rule_category: StrategyRuleCategory
    required_fields: list[str] = Field(default_factory=list)
    violation_code: str
    needs_data_behavior: NeedsDataBehavior = "needs_data"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("rule_id", "name", "description", "violation_code")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @field_validator("required_fields")
    @classmethod
    def _clean_fields(cls, fields: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for field in fields:
            value = field.strip()
            if value and value not in seen:
                cleaned.append(value)
                seen.add(value)
        return cleaned


class StrategyRuleViolation(BaseModel):
    violation_id: str
    evaluation_id: str
    review_id: str | None = None
    rule_id: str
    journal_id: int | None = None
    symbol: str | None = None
    violation_code: str
    violation_detail: str
    evidence: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    created_at: datetime


class StrategyRuleEvaluation(BaseModel):
    evaluation_id: str
    review_id: str | None = None
    rule_id: str
    journal_id: int | None = None
    symbol: str | None = None
    evaluation_status: StrategyEvaluationStatus
    evaluated_at: datetime
    evidence: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    reason: str
    violations: list[StrategyRuleViolation] = Field(default_factory=list)


def forbidden_strategy_signal_terms() -> list[str]:
    return [
        "buy",
        "sell",
        "hold",
        "strong buy",
        "safe",
        "guaranteed",
        "predicted winner",
        "best pick",
        "recommendation",
    ]
