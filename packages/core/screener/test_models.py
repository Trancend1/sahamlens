from __future__ import annotations

from datetime import UTC, datetime

from packages.core.fundamentals.models import build_fundamental_snapshot
from packages.core.screener.models import (
    ScreenerCandidate,
    ScreenerCondition,
    ScreenerRule,
    forbidden_signal_terms,
)
from packages.core.ticker_coverage.models import SourceCoverageSnapshot, classify_ticker_coverage

NOW = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)


def test_screener_rule_keeps_explicit_no_signal_metadata() -> None:
    rule = ScreenerRule(
        rule_id="fundamentals-basic",
        name="Fundamental completeness filter",
        description="Filters symbols with visible coverage and fundamental fields.",
        required_fields=["market_cap", "roe"],
        required_source_types=["ohlcv", "fundamental"],
        min_coverage_tier="tier_b",
        allowed_freshness_states=["fresh", "delayed"],
        min_fundamental_completeness="partial",
        min_confidence_level="medium",
        conditions=[
            ScreenerCondition(
                condition_id="roe-exists",
                field_name="roe",
                operator="exists",
                missing_behavior="exclude",
            )
        ],
    )

    rendered = f"{rule.name} {rule.description}".lower()

    assert rule.min_coverage_tier == "tier_b"
    assert rule.conditions[0].field_name == "roe"
    assert not any(term in rendered for term in forbidden_signal_terms())


def test_candidate_uses_ohlcv_freshness_and_fundamental_fields() -> None:
    lifecycle = classify_ticker_coverage(
        symbol="BBCA",
        lifecycle_status="active",
        ohlcv_available=True,
        ohlcv_freshness_state="delayed",
        provider_health_visible=True,
        fundamental_completeness="partial",
        source="manual",
        checked_at=NOW,
    )
    source = SourceCoverageSnapshot(
        symbol="BBCA",
        provider_name="yfinance",
        source_type="ohlcv",
        provider_trust_tier="tier_3",
        availability_state="available",
        freshness_state="delayed",
        last_checked_at=NOW,
    )
    fundamental = build_fundamental_snapshot(
        symbol="BBCA",
        period="2026Q1",
        source="manual",
        source_type="manual",
        data_fields={"market_cap": 1_000_000, "roe": 0.18},
        required_fields=["market_cap", "roe", "pe_ratio", "pbv"],
        coverage_tier="tier_b",
        freshness_state="delayed",
        provider_trust_tier="tier_3",
        fetched_at=NOW,
        imported_at=NOW,
    )

    candidate = ScreenerCandidate(
        symbol="bbca",
        coverage=lifecycle,
        source_coverage=[source],
        fundamental=fundamental,
    )

    assert candidate.symbol == "BBCA.JK"
    assert candidate.freshness_state == "delayed"
    assert candidate.resolve_field("roe") == 0.18
    assert candidate.resolve_field("coverage_tier") == "tier_a"
