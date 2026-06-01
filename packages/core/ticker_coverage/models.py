"""Ticker lifecycle and coverage classification for V1-S2."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from packages.core.data_quality.models import FreshnessState, ProviderTrustTier, SourceType
from packages.core.data_sources.normalize import normalize_ticker
from pydantic import BaseModel, Field, field_validator

LifecycleStatus = Literal["active", "suspended", "delisted", "renamed", "unknown"]
CoverageTier = Literal["tier_a", "tier_b", "tier_c"]
AvailabilityState = Literal["available", "partial", "missing", "failed", "unknown"]
FundamentalCompleteness = Literal["complete", "partial", "sparse", "missing"]


class TickerLifecycleSnapshot(BaseModel):
    symbol: str
    lifecycle_status: LifecycleStatus
    coverage_tier: CoverageTier
    lifecycle_source: str
    coverage_source: str
    last_verified_at: datetime
    renamed_from: str | None = None
    renamed_to: str | None = None
    missing_data_reason: str | None = None
    screener_eligible: bool = False
    alert_eligible: bool = False
    ai_explanation_eligible: bool = False
    eligibility_reason: str | None = None
    updated_at: datetime

    @field_validator("symbol", "renamed_from", "renamed_to")
    @classmethod
    def _canon_optional_symbol(cls, value: str | None) -> str | None:
        return normalize_ticker(value) if value else None

    @field_validator("lifecycle_source", "coverage_source")
    @classmethod
    def _required_source(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("source must not be blank")
        return cleaned


class SourceCoverageSnapshot(BaseModel):
    symbol: str
    provider_name: str
    source_type: SourceType
    provider_trust_tier: ProviderTrustTier
    availability_state: AvailabilityState
    freshness_state: FreshnessState
    last_success_at: datetime | None = None
    last_checked_at: datetime
    missing_reason: str | None = None
    coverage_count: int | None = Field(default=None, ge=0)

    @field_validator("symbol")
    @classmethod
    def _canon(cls, value: str) -> str:
        return normalize_ticker(value)

    @field_validator("provider_name")
    @classmethod
    def _provider_name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("provider_name must not be blank")
        return cleaned

    @property
    def supports_dependent_flows(self) -> bool:
        return self.availability_state in {"available", "partial"} and self.freshness_state in {
            "fresh",
            "delayed",
        }

    @property
    def requires_caveat(self) -> bool:
        return self.provider_trust_tier in {"tier_3", "tier_4"} or not self.supports_dependent_flows


def classify_ticker_coverage(
    *,
    symbol: str,
    lifecycle_status: LifecycleStatus,
    ohlcv_available: bool,
    ohlcv_freshness_state: FreshnessState,
    provider_health_visible: bool,
    fundamental_completeness: FundamentalCompleteness | None,
    source: str,
    checked_at: datetime,
    renamed_from: str | None = None,
    renamed_to: str | None = None,
) -> TickerLifecycleSnapshot:
    canonical = normalize_ticker(symbol)
    tier, reason = _derive_tier(
        lifecycle_status=lifecycle_status,
        ohlcv_available=ohlcv_available,
        ohlcv_freshness_state=ohlcv_freshness_state,
        provider_health_visible=provider_health_visible,
        fundamental_completeness=fundamental_completeness,
        renamed_to=renamed_to,
    )
    screener_eligible = tier in {"tier_a", "tier_b"} and lifecycle_status == "active"
    alert_eligible = tier in {"tier_a", "tier_b"} and lifecycle_status == "active"
    ai_explanation_eligible = tier in {"tier_a", "tier_b"}
    return TickerLifecycleSnapshot(
        symbol=canonical,
        lifecycle_status=lifecycle_status,
        coverage_tier=tier,
        lifecycle_source=source,
        coverage_source=source,
        last_verified_at=checked_at,
        renamed_from=renamed_from,
        renamed_to=renamed_to,
        missing_data_reason=reason if tier != "tier_a" else None,
        screener_eligible=screener_eligible,
        alert_eligible=alert_eligible,
        ai_explanation_eligible=ai_explanation_eligible,
        eligibility_reason=reason,
        updated_at=checked_at,
    )


def _derive_tier(
    *,
    lifecycle_status: LifecycleStatus,
    ohlcv_available: bool,
    ohlcv_freshness_state: FreshnessState,
    provider_health_visible: bool,
    fundamental_completeness: FundamentalCompleteness | None,
    renamed_to: str | None,
) -> tuple[CoverageTier, str]:
    if lifecycle_status == "delisted":
        return "tier_c", "delisted ticker is historical only"
    if lifecycle_status == "unknown":
        return "tier_c", "unknown lifecycle status requires manual verification"
    if lifecycle_status == "suspended":
        return "tier_c", "suspended ticker is restricted to data-quality checks"
    if lifecycle_status == "renamed" and not renamed_to:
        return "tier_c", "renamed ticker requires alias mapping"
    if not provider_health_visible:
        return "tier_c", "provider health is not visible"
    if not ohlcv_available:
        return "tier_c", "ohlcv coverage is missing"
    if ohlcv_freshness_state in {"failed", "unknown", "stale"}:
        return "tier_c", f"ohlcv freshness is {ohlcv_freshness_state}"
    if lifecycle_status == "renamed":
        return "tier_b", "renamed ticker needs alias caveat"
    if ohlcv_freshness_state == "partial":
        return "tier_b", "ohlcv coverage is partial"
    if fundamental_completeness in {"sparse", "missing", None}:
        return "tier_b", f"fundamental completeness is {fundamental_completeness or 'missing'}"
    return "tier_a", "full support with visible caveats"
