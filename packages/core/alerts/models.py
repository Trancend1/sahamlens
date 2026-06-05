"""Local alert lifecycle models for V1-S6."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, Self

from packages.core.data_quality.models import FreshnessState
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.fundamentals.models import ConfidenceLevel
from pydantic import BaseModel, Field, field_validator, model_validator

AlertRuleType = Literal["price_above", "price_below", "volume_above"]
AlertDefinitionStatus = Literal["active", "paused", "archived"]
AlertEvaluationStatus = Literal[
    "success",
    "skipped_stale_data",
    "skipped_low_confidence",
    "failed_provider",
    "failed_runtime",
    "no_match",
]
AlertEventStatus = Literal[
    "new",
    "acknowledged",
    "dismissed",
    "marked_false_positive",
    "resolved",
]
AlertSeverity = Literal["info", "warning", "critical"]
AlertDeliveryStatus = Literal["disabled", "skipped_not_configured", "sent", "failed"]

SUPPORTED_RULE_TYPES: frozenset[str] = frozenset({"price_above", "price_below", "volume_above"})
ALLOWED_FRESHNESS_FOR_ALERTS: frozenset[FreshnessState] = frozenset({"fresh", "delayed"})
ALLOWED_CONFIDENCE_FOR_ALERTS: frozenset[ConfidenceLevel] = frozenset({"high", "medium"})


class AlertRuleInput(BaseModel):
    name: str
    description: str
    rule_type: AlertRuleType
    ticker: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    now: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("name", "description")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @field_validator("ticker")
    @classmethod
    def _canon_ticker(cls, value: str) -> str:
        return normalize_ticker(value)

    @field_validator("rule_type", mode="before")
    @classmethod
    def _supported_rule_type(cls, value: object) -> object:
        if str(value) not in SUPPORTED_RULE_TYPES:
            raise ValueError("unsupported alert rule type")
        return value

    @model_validator(mode="after")
    def _valid_parameters(self) -> Self:
        _threshold(self.parameters)
        return self


class AlertRule(BaseModel):
    id: str
    name: str
    description: str
    rule_type: AlertRuleType
    ticker: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None

    @field_validator("ticker")
    @classmethod
    def _canon_ticker(cls, value: str) -> str:
        return normalize_ticker(value)

    @property
    def definition_status(self) -> AlertDefinitionStatus:
        if self.archived_at is not None:
            return "archived"
        return "active" if self.is_active else "paused"


class AlertEvaluation(BaseModel):
    id: str
    rule_id: str
    ticker: str
    evaluated_at: datetime
    status: AlertEvaluationStatus
    reason: str
    data_freshness_status: FreshnessState
    confidence_status: ConfidenceLevel
    matched: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class AlertEvent(BaseModel):
    id: str
    rule_id: str
    evaluation_id: str
    ticker: str
    event_type: AlertRuleType
    severity: AlertSeverity = "info"
    title: str
    message: str
    status: AlertEventStatus = "new"
    created_at: datetime
    acknowledged_at: datetime | None = None
    dismissed_at: datetime | None = None
    false_positive_at: datetime | None = None
    resolved_at: datetime | None = None
    notes: str | None = None

    @field_validator("ticker")
    @classmethod
    def _canon_ticker(cls, value: str) -> str:
        return normalize_ticker(value)


class AlertDeliveryAttempt(BaseModel):
    id: str
    event_id: str
    channel: Literal["telegram"]
    status: AlertDeliveryStatus
    attempted_at: datetime
    error_code: str | None = None
    error_message: str | None = None
    redacted_details: dict[str, Any] = Field(default_factory=dict)


class AlertEvaluationResult(BaseModel):
    evaluated_count: int
    event_count: int
    evaluations: list[AlertEvaluation] = Field(default_factory=list)
    events: list[AlertEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AlertEvaluationInput(BaseModel):
    rule: AlertRule
    latest_close: float | None = None
    latest_volume: int | None = None
    data_freshness_status: FreshnessState = "unknown"
    confidence_status: ConfidenceLevel = "none"
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def threshold_value(rule: AlertRule | AlertRuleInput) -> float:
    return _threshold(rule.parameters)


def _threshold(parameters: dict[str, Any]) -> float:
    raw = parameters.get("threshold")
    if raw is None:
        raise ValueError("threshold parameter is required")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("threshold parameter must be numeric") from exc
    if value < 0:
        raise ValueError("threshold parameter must be non-negative")
    return value
