from __future__ import annotations

from datetime import UTC, date, datetime

from packages.core.fundamentals.models import (
    FundamentalSnapshot,
    build_fundamental_snapshot,
    calculate_completeness,
    calculate_confidence,
)

NOW = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
REQUIRED = ["market_cap", "pe_ratio", "pbv", "roe"]


def test_calculate_completeness_complete_partial_sparse_missing() -> None:
    assert calculate_completeness(
        REQUIRED, {"market_cap": 1, "pe_ratio": 2, "pbv": 3, "roe": 4}
    ) == (
        "complete",
        ["market_cap", "pe_ratio", "pbv", "roe"],
        [],
    )
    assert calculate_completeness(REQUIRED, {"market_cap": 1, "roe": 4}) == (
        "partial",
        ["market_cap", "roe"],
        ["pe_ratio", "pbv"],
    )
    assert calculate_completeness(REQUIRED, {"market_cap": 1}) == (
        "sparse",
        ["market_cap"],
        ["pe_ratio", "pbv", "roe"],
    )
    assert calculate_completeness(REQUIRED, {}) == (
        "missing",
        [],
        ["market_cap", "pe_ratio", "pbv", "roe"],
    )


def test_calculate_confidence_uses_coverage_freshness_trust_and_completeness() -> None:
    high = calculate_confidence(
        coverage_tier="tier_a",
        freshness_state="fresh",
        provider_trust_tier="tier_1",
        completeness_state="complete",
    )
    low = calculate_confidence(
        coverage_tier="tier_c",
        freshness_state="unknown",
        provider_trust_tier="tier_3",
        completeness_state="sparse",
    )

    assert high.level == "high"
    assert high.score > low.score
    assert low.level == "low"


def test_sparse_completeness_caps_confidence_at_low() -> None:
    confidence = calculate_confidence(
        coverage_tier="tier_b",
        freshness_state="delayed",
        provider_trust_tier="tier_2",
        completeness_state="sparse",
    )

    assert confidence.level == "low"


def test_build_fundamental_snapshot_normalizes_fields_and_caveats() -> None:
    snapshot = build_fundamental_snapshot(
        symbol="bbca",
        period="2026Q1",
        source="manual",
        source_type="manual",
        data_fields={"market_cap": 1_000_000, "roe": 0.18},
        required_fields=REQUIRED,
        coverage_tier="tier_b",
        freshness_state="delayed",
        provider_trust_tier="tier_3",
        fetched_at=NOW,
        imported_at=NOW,
    )

    assert snapshot.symbol == "BBCA.JK"
    assert snapshot.completeness_state == "partial"
    assert snapshot.confidence_level == "medium"
    assert snapshot.available_fields == ["market_cap", "roe"]
    assert snapshot.missing_fields == ["pe_ratio", "pbv"]
    assert "missing" in (snapshot.caveat or "").lower()


def test_missing_snapshot_has_no_confidence() -> None:
    snapshot = FundamentalSnapshot(
        symbol="TLKM",
        period="2026Q1",
        statement_date=date(2026, 3, 31),
        source="manual",
        source_type="manual",
        fetched_at=NOW,
        imported_at=NOW,
        data_fields={},
        available_fields=[],
        missing_fields=REQUIRED,
        completeness_state="missing",
        confidence_level="none",
        confidence_score=0,
        caveat="No usable fundamental snapshot.",
    )

    assert snapshot.symbol == "TLKM.JK"
    assert snapshot.usable_for_fundamental_rules is False
