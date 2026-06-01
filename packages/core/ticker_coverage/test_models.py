from __future__ import annotations

from datetime import UTC, datetime

from packages.core.ticker_coverage.models import (
    SourceCoverageSnapshot,
    classify_ticker_coverage,
)

NOW = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)


def test_active_ticker_with_fresh_ohlcv_and_partial_fundamentals_is_tier_a() -> None:
    snapshot = classify_ticker_coverage(
        symbol="bbca",
        lifecycle_status="active",
        ohlcv_available=True,
        ohlcv_freshness_state="fresh",
        provider_health_visible=True,
        fundamental_completeness="partial",
        source="manual",
        checked_at=NOW,
    )

    assert snapshot.symbol == "BBCA.JK"
    assert snapshot.coverage_tier == "tier_a"
    assert snapshot.screener_eligible is True
    assert snapshot.alert_eligible is True
    assert snapshot.ai_explanation_eligible is True


def test_unknown_ticker_defaults_to_tier_c_and_restricted() -> None:
    snapshot = classify_ticker_coverage(
        symbol="tlkm",
        lifecycle_status="unknown",
        ohlcv_available=True,
        ohlcv_freshness_state="fresh",
        provider_health_visible=True,
        fundamental_completeness="complete",
        source="manual",
        checked_at=NOW,
    )

    assert snapshot.coverage_tier == "tier_c"
    assert snapshot.screener_eligible is False
    assert snapshot.alert_eligible is False
    assert snapshot.ai_explanation_eligible is False
    assert snapshot.eligibility_reason is not None
    assert "unknown" in snapshot.eligibility_reason.lower()


def test_sparse_fundamentals_keep_active_ticker_in_tier_b() -> None:
    snapshot = classify_ticker_coverage(
        symbol="tlkm",
        lifecycle_status="active",
        ohlcv_available=True,
        ohlcv_freshness_state="delayed",
        provider_health_visible=True,
        fundamental_completeness="sparse",
        source="manual",
        checked_at=NOW,
    )

    assert snapshot.coverage_tier == "tier_b"
    assert snapshot.screener_eligible is True
    assert snapshot.alert_eligible is True
    assert snapshot.ai_explanation_eligible is True
    assert snapshot.missing_data_reason is not None
    assert "sparse" in snapshot.missing_data_reason.lower()


def test_delisted_ticker_is_never_decision_flow_eligible() -> None:
    snapshot = classify_ticker_coverage(
        symbol="asii",
        lifecycle_status="delisted",
        ohlcv_available=True,
        ohlcv_freshness_state="fresh",
        provider_health_visible=True,
        fundamental_completeness="complete",
        source="manual",
        checked_at=NOW,
    )

    assert snapshot.coverage_tier == "tier_c"
    assert snapshot.screener_eligible is False
    assert snapshot.alert_eligible is False
    assert snapshot.ai_explanation_eligible is False


def test_source_coverage_exposes_dependent_flow_readiness() -> None:
    coverage = SourceCoverageSnapshot(
        symbol="BBCA",
        provider_name="yfinance",
        source_type="ohlcv",
        provider_trust_tier="tier_3",
        availability_state="available",
        freshness_state="fresh",
        last_success_at=NOW,
        last_checked_at=NOW,
        coverage_count=1,
    )

    assert coverage.symbol == "BBCA.JK"
    assert coverage.supports_dependent_flows is True
    assert coverage.requires_caveat is True
