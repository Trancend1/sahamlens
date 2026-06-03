"""Transparent screener rule and result models for V1-S3."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from packages.core.data_quality.models import FreshnessState, SourceType
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.fundamentals.models import (
    CompletenessState,
    ConfidenceLevel,
    FundamentalSnapshot,
)
from packages.core.ticker_coverage.models import (
    CoverageTier,
    LifecycleStatus,
    SourceCoverageSnapshot,
    TickerLifecycleSnapshot,
)
from pydantic import BaseModel, Field, field_validator

ConditionOperator = Literal["gt", "gte", "lt", "lte", "eq", "neq", "exists", "between"]
MissingBehavior = Literal["exclude", "caveat"]
RunStatus = Literal["running", "completed", "failed", "partial"]
ResultStatus = Literal["included", "excluded"]


def _default_freshness_states() -> list[FreshnessState]:
    return ["fresh", "delayed"]


class ScreenerCondition(BaseModel):
    condition_id: str
    field_name: str
    operator: ConditionOperator
    value: Any | None = None
    required_source_type: SourceType | None = None
    missing_behavior: MissingBehavior = "exclude"
    description: str | None = None

    @field_validator("condition_id", "field_name")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @property
    def label(self) -> str:
        if self.operator == "exists":
            return f"{self.field_name} exists"
        return f"{self.field_name} {self.operator}"


class ScreenerRule(BaseModel):
    rule_id: str
    name: str
    description: str
    required_fields: list[str] = Field(default_factory=list)
    required_source_types: list[SourceType] = Field(default_factory=list)
    min_coverage_tier: CoverageTier = "tier_b"
    allowed_freshness_states: list[FreshnessState] = Field(
        default_factory=_default_freshness_states
    )
    min_fundamental_completeness: CompletenessState | None = None
    min_confidence_level: ConfidenceLevel | None = None
    conditions: list[ScreenerCondition] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("rule_id", "name", "description")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @field_validator("required_fields")
    @classmethod
    def _clean_fields(cls, fields: list[str]) -> list[str]:
        return _unique_clean(fields)


class ScreenerCandidate(BaseModel):
    symbol: str
    coverage: TickerLifecycleSnapshot | None = None
    source_coverage: list[SourceCoverageSnapshot] = Field(default_factory=list)
    fundamental: FundamentalSnapshot | None = None
    price_fields: dict[str, Any] = Field(default_factory=dict)
    indicator_fields: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    @classmethod
    def _canon(cls, value: str) -> str:
        return normalize_ticker(value)

    @property
    def freshness_state(self) -> FreshnessState:
        ohlcv_sources = [source for source in self.source_coverage if source.source_type == "ohlcv"]
        if ohlcv_sources:
            return ohlcv_sources[0].freshness_state
        if self.source_coverage:
            return self.source_coverage[0].freshness_state
        return "unknown"

    def resolve_field(self, field_name: str) -> Any | None:
        metadata = {
            "symbol": self.symbol,
            "coverage_tier": self.coverage.coverage_tier if self.coverage else None,
            "lifecycle_status": self.coverage.lifecycle_status if self.coverage else None,
            "freshness_state": self.freshness_state,
            "completeness_state": self.fundamental.completeness_state if self.fundamental else None,
            "confidence_level": self.fundamental.confidence_level if self.fundamental else None,
        }
        if field_name in metadata:
            return metadata[field_name]
        if self.fundamental and field_name in self.fundamental.data_fields:
            return self.fundamental.data_fields[field_name]
        if field_name in self.price_fields:
            return self.price_fields[field_name]
        if field_name in self.indicator_fields:
            return self.indicator_fields[field_name]
        return None


class ScreenerExclusion(BaseModel):
    reason_code: str
    reason_detail: str
    source_field: str | None = None


class ScreenerResult(BaseModel):
    run_id: str
    symbol: str
    result_status: ResultStatus
    coverage_tier: CoverageTier
    lifecycle_status: LifecycleStatus
    freshness_state: FreshnessState
    completeness_state: CompletenessState | None = None
    confidence_level: ConfidenceLevel | None = None
    matched_conditions: list[str] = Field(default_factory=list)
    failed_conditions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    exclusion_reasons: list[str] = Field(default_factory=list)
    exclusions: list[ScreenerExclusion] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    explanation: str
    evaluated_at: datetime

    @field_validator("symbol")
    @classmethod
    def _canon(cls, value: str) -> str:
        return normalize_ticker(value)


class ScreenerRun(BaseModel):
    run_id: str
    rule: ScreenerRule
    started_at: datetime
    completed_at: datetime | None = None
    status: RunStatus = "running"
    universe_count: int = 0
    included_count: int = 0
    excluded_count: int = 0
    data_quality_snapshot: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    results: list[ScreenerResult] = Field(default_factory=list)


def forbidden_signal_terms() -> list[str]:
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


def _unique_clean(fields: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for field in fields:
        value = field.strip()
        if value and value not in seen:
            cleaned.append(value)
            seen.add(value)
    return cleaned
