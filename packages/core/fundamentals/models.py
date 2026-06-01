"""Fundamental snapshot completeness and confidence for V1-S2."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from packages.core.data_quality.models import FreshnessState, ProviderTrustTier
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.ticker_coverage.models import CoverageTier
from pydantic import BaseModel, Field, field_validator

FundamentalSourceType = Literal["manual", "official", "public_provider", "other"]
CompletenessState = Literal["complete", "partial", "sparse", "missing"]
ConfidenceLevel = Literal["high", "medium", "low", "none"]


class ConfidenceResult(BaseModel):
    level: ConfidenceLevel
    score: float = Field(ge=0, le=1)


class FundamentalSnapshot(BaseModel):
    symbol: str
    period: str
    statement_date: date | None = None
    source: str
    source_type: FundamentalSourceType
    fetched_at: datetime
    imported_at: datetime
    data_fields: dict[str, Any] = Field(default_factory=dict)
    available_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    completeness_state: CompletenessState
    confidence_level: ConfidenceLevel
    confidence_score: float = Field(ge=0, le=1)
    caveat: str | None = None
    reason: str | None = None

    @field_validator("symbol")
    @classmethod
    def _canon(cls, value: str) -> str:
        return normalize_ticker(value)

    @field_validator("period", "source")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @field_validator("available_fields", "missing_fields")
    @classmethod
    def _sort_fields(cls, value: list[str]) -> list[str]:
        return _unique_clean(value)

    @property
    def usable_for_fundamental_rules(self) -> bool:
        return self.completeness_state in {"complete", "partial"} and self.confidence_level in {
            "high",
            "medium",
        }


def calculate_completeness(
    required_fields: list[str],
    data_fields: dict[str, Any],
) -> tuple[CompletenessState, list[str], list[str]]:
    normalized_required = _unique_clean(required_fields)
    available = [
        field
        for field in normalized_required
        if field in data_fields and data_fields[field] not in {None, ""}
    ]
    missing = [field for field in normalized_required if field not in available]
    if not available:
        return "missing", [], missing
    if not missing:
        return "complete", available, []
    if len(available) >= max(2, len(normalized_required) // 2):
        return "partial", available, missing
    return "sparse", available, missing


def calculate_confidence(
    *,
    coverage_tier: CoverageTier,
    freshness_state: FreshnessState,
    provider_trust_tier: ProviderTrustTier,
    completeness_state: CompletenessState,
) -> ConfidenceResult:
    score = (
        _coverage_score(coverage_tier)
        + _freshness_score(freshness_state)
        + _trust_score(provider_trust_tier)
        + _completeness_score(completeness_state)
    ) / 4
    rounded = round(score, 3)
    if completeness_state == "missing" or rounded <= 0:
        return ConfidenceResult(level="none", score=0)
    if rounded >= 0.75:
        return ConfidenceResult(level="high", score=rounded)
    if rounded >= 0.5:
        return ConfidenceResult(level="medium", score=rounded)
    return ConfidenceResult(level="low", score=rounded)


def build_fundamental_snapshot(
    *,
    symbol: str,
    period: str,
    source: str,
    source_type: FundamentalSourceType,
    data_fields: dict[str, Any],
    required_fields: list[str],
    coverage_tier: CoverageTier,
    freshness_state: FreshnessState,
    provider_trust_tier: ProviderTrustTier,
    fetched_at: datetime,
    imported_at: datetime,
    statement_date: date | None = None,
) -> FundamentalSnapshot:
    completeness, available, missing = calculate_completeness(required_fields, data_fields)
    confidence = calculate_confidence(
        coverage_tier=coverage_tier,
        freshness_state=freshness_state,
        provider_trust_tier=provider_trust_tier,
        completeness_state=completeness,
    )
    return FundamentalSnapshot(
        symbol=symbol,
        period=period,
        statement_date=statement_date,
        source=source,
        source_type=source_type,
        fetched_at=fetched_at,
        imported_at=imported_at,
        data_fields=data_fields,
        available_fields=available,
        missing_fields=missing,
        completeness_state=completeness,
        confidence_level=confidence.level,
        confidence_score=confidence.score,
        caveat=_build_caveat(missing, confidence.level),
        reason=_build_reason(completeness, confidence.level),
    )


def _coverage_score(tier: CoverageTier) -> float:
    return {"tier_a": 0.9, "tier_b": 0.55, "tier_c": 0.2}[tier]


def _freshness_score(state: FreshnessState) -> float:
    return {
        "fresh": 0.9,
        "delayed": 0.75,
        "partial": 0.5,
        "stale": 0.3,
        "failed": 0.1,
        "unknown": 0.1,
    }[state]


def _trust_score(tier: ProviderTrustTier) -> float:
    return {"tier_1": 0.95, "tier_2": 0.8, "tier_3": 0.55, "tier_4": 0.25}[tier]


def _completeness_score(state: CompletenessState) -> float:
    return {"complete": 0.9, "partial": 0.65, "sparse": 0.35, "missing": 0.0}[state]


def _build_caveat(missing: list[str], confidence: ConfidenceLevel) -> str | None:
    parts: list[str] = []
    if missing:
        parts.append(f"Missing fields: {', '.join(missing)}.")
    if confidence in {"low", "none"}:
        parts.append("Low confidence; do not infer fundamentals.")
    return " ".join(parts) or None


def _build_reason(completeness: CompletenessState, confidence: ConfidenceLevel) -> str:
    return f"completeness={completeness}; confidence={confidence}"


def _unique_clean(fields: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for field in fields:
        value = field.strip()
        if value and value not in seen:
            cleaned.append(value)
            seen.add(value)
    return cleaned
