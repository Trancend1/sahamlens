"""Provider health and freshness models for V1 data quality."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

FreshnessState = Literal["fresh", "delayed", "stale", "failed", "partial", "unknown"]
ProviderTrustTier = Literal["tier_1", "tier_2", "tier_3", "tier_4"]
SourceType = Literal["ohlcv", "fundamental", "news", "delivery", "manual", "other"]

_DEPENDENT_FLOW_STATES: frozenset[FreshnessState] = frozenset({"fresh", "delayed"})
_CAVEAT_TRUST_TIERS: frozenset[ProviderTrustTier] = frozenset({"tier_3", "tier_4"})


class ProviderHealthSnapshot(BaseModel):
    provider_name: str
    provider_trust_tier: ProviderTrustTier
    source_type: SourceType
    freshness_state: FreshnessState
    updated_at: datetime
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_failure_reason: str | None = None
    consecutive_failure_count: int = Field(default=0, ge=0)
    coverage_count: int | None = Field(default=None, ge=0)

    @field_validator("provider_name")
    @classmethod
    def _provider_name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("provider_name must not be blank")
        return cleaned

    @field_validator("last_failure_reason")
    @classmethod
    def _blank_failure_reason_as_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def _validate_state_timestamps(self) -> Self:
        if self.freshness_state in {"fresh", "delayed", "stale", "partial"} and (
            self.last_success_at is None
        ):
            raise ValueError(f"{self.freshness_state} requires last_success_at")
        if self.freshness_state == "failed" and self.last_failure_at is None:
            raise ValueError("failed requires last_failure_at")
        if self.consecutive_failure_count > 0 and self.last_failure_at is None:
            raise ValueError("consecutive failures require last_failure_at")
        return self

    @property
    def supports_dependent_flows(self) -> bool:
        """True when downstream screener/alert-style flows may proceed."""
        return self.freshness_state in _DEPENDENT_FLOW_STATES

    @property
    def requires_caveat(self) -> bool:
        return self.freshness_state != "fresh" or self.provider_trust_tier in _CAVEAT_TRUST_TIERS

    @property
    def has_visible_failure(self) -> bool:
        return self.last_failure_at is not None or self.consecutive_failure_count > 0


class DataQualityOverview(BaseModel):
    providers: list[ProviderHealthSnapshot] = Field(default_factory=list)

    @property
    def provider_count(self) -> int:
        return len(self.providers)

    @property
    def failed_provider_count(self) -> int:
        return sum(1 for provider in self.providers if provider.freshness_state == "failed")

    @property
    def stale_provider_count(self) -> int:
        return sum(1 for provider in self.providers if provider.freshness_state == "stale")

    @property
    def restricted_provider_count(self) -> int:
        return sum(1 for provider in self.providers if not provider.supports_dependent_flows)

    @property
    def total_coverage_count(self) -> int:
        return sum(provider.coverage_count or 0 for provider in self.providers)
