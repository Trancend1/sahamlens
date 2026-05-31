"""Tests for V1 data quality provider health models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from packages.core.data_quality.models import DataQualityOverview, ProviderHealthSnapshot
from pydantic import ValidationError

NOW = datetime(2026, 5, 31, 9, 0, tzinfo=UTC)
EARLIER = datetime(2026, 5, 31, 8, 0, tzinfo=UTC)


def _snapshot(
    freshness_state: str,
    *,
    trust_tier: str = "tier_3",
    coverage_count: int | None = 10,
) -> ProviderHealthSnapshot:
    kwargs: dict[str, object] = {
        "provider_name": " yfinance ",
        "provider_trust_tier": trust_tier,
        "source_type": "ohlcv",
        "freshness_state": freshness_state,
        "updated_at": NOW,
        "coverage_count": coverage_count,
    }
    if freshness_state in {"fresh", "delayed", "stale", "partial"}:
        kwargs["last_success_at"] = EARLIER
    if freshness_state == "failed":
        kwargs["last_failure_at"] = NOW
        kwargs["last_failure_reason"] = " 429 rate limited "
        kwargs["consecutive_failure_count"] = 1
    return ProviderHealthSnapshot.model_validate(kwargs)


def test_provider_name_and_failure_reason_are_cleaned() -> None:
    snapshot = _snapshot("failed")
    assert snapshot.provider_name == "yfinance"
    assert snapshot.last_failure_reason == "429 rate limited"


@pytest.mark.parametrize("state", ["fresh", "delayed"])
def test_fresh_and_delayed_support_dependent_flows(state: str) -> None:
    assert _snapshot(state).supports_dependent_flows is True


@pytest.mark.parametrize("state", ["stale", "failed", "partial", "unknown"])
def test_non_ready_states_restrict_dependent_flows(state: str) -> None:
    assert _snapshot(state, coverage_count=None).supports_dependent_flows is False


def test_tier_three_provider_requires_caveat_even_when_fresh() -> None:
    assert _snapshot("fresh", trust_tier="tier_3").requires_caveat is True


def test_tier_one_fresh_provider_does_not_require_caveat() -> None:
    assert _snapshot("fresh", trust_tier="tier_1").requires_caveat is False


def test_success_states_require_last_success_timestamp() -> None:
    with pytest.raises(ValidationError, match="fresh requires last_success_at"):
        ProviderHealthSnapshot(
            provider_name="manual",
            provider_trust_tier="tier_1",
            source_type="manual",
            freshness_state="fresh",
            updated_at=NOW,
        )


def test_failed_state_requires_last_failure_timestamp() -> None:
    with pytest.raises(ValidationError, match="failed requires last_failure_at"):
        ProviderHealthSnapshot(
            provider_name="yfinance",
            provider_trust_tier="tier_3",
            source_type="ohlcv",
            freshness_state="failed",
            updated_at=NOW,
        )


def test_overview_counts_provider_states_and_coverage() -> None:
    overview = DataQualityOverview(
        providers=[
            _snapshot("fresh", coverage_count=3),
            _snapshot("stale", coverage_count=2),
            _snapshot("failed", coverage_count=None),
        ]
    )
    assert overview.provider_count == 3
    assert overview.stale_provider_count == 1
    assert overview.failed_provider_count == 1
    assert overview.restricted_provider_count == 2
    assert overview.total_coverage_count == 5


def test_properties_expose_ui_ready_fields() -> None:
    overview = DataQualityOverview(providers=[_snapshot("failed", coverage_count=None)])

    assert overview.provider_count == 1
    assert overview.failed_provider_count == 1
    assert overview.providers[0].supports_dependent_flows is False
    assert overview.providers[0].requires_caveat is True
