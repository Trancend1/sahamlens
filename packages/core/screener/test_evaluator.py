from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from packages.core.data_quality.models import FreshnessState
from packages.core.fundamentals.models import CompletenessState, build_fundamental_snapshot
from packages.core.screener.evaluator import evaluate_screener_rule
from packages.core.screener.models import (
    ScreenerCandidate,
    ScreenerCondition,
    ScreenerRule,
    forbidden_signal_terms,
)
from packages.core.ticker_coverage.models import (
    LifecycleStatus,
    SourceCoverageSnapshot,
    classify_ticker_coverage,
)

NOW = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)


def test_evaluator_includes_symbol_that_passes_all_gates() -> None:
    result = evaluate_screener_rule(
        _rule(),
        [_candidate("BBCA", tier_input_fundamentals="partial")],
        run_id="run-1",
        evaluated_at=NOW,
    ).results[0]

    assert result.result_status == "included"
    assert result.matched_conditions == ["market_cap exists", "roe exists"]
    assert result.exclusion_reasons == []
    assert "matched filter" in result.explanation.lower()


def test_evaluator_excludes_tier_c_and_lifecycle_restricted_symbols() -> None:
    results = evaluate_screener_rule(
        _rule(),
        [
            _candidate("TLKM", ohlcv_available=False),
            _candidate("GOTO", lifecycle_status="suspended"),
        ],
        run_id="run-1",
        evaluated_at=NOW,
    ).results

    assert [result.result_status for result in results] == ["excluded", "excluded"]
    assert any("coverage tier tier_c" in reason for reason in results[0].exclusion_reasons)
    assert any("lifecycle suspended" in reason for reason in results[1].exclusion_reasons)


def test_evaluator_excludes_stale_freshness_and_missing_required_fields() -> None:
    results = evaluate_screener_rule(
        _rule(),
        [
            _candidate("BBCA", freshness_state="stale"),
            _candidate("BMRI", fields={"market_cap": 1_000_000}),
        ],
        run_id="run-1",
        evaluated_at=NOW,
    ).results

    assert any("freshness stale" in reason for reason in results[0].exclusion_reasons)
    assert results[1].missing_fields == ["roe"]
    assert any("missing required field roe" in reason for reason in results[1].exclusion_reasons)


def test_evaluator_excludes_low_confidence_fundamentals() -> None:
    result = evaluate_screener_rule(
        _rule(),
        [
            _candidate(
                "BBCA", fields={"market_cap": 1_000_000}, required_fields=["market_cap", "roe"]
            )
        ],
        run_id="run-1",
        evaluated_at=NOW,
    ).results[0]

    assert result.result_status == "excluded"
    assert result.confidence_level == "low"
    assert any("confidence low" in reason for reason in result.exclusion_reasons)


def test_evaluator_explanations_do_not_use_forbidden_signal_copy() -> None:
    run = evaluate_screener_rule(
        _rule(),
        [_candidate("BBCA", tier_input_fundamentals="partial")],
        run_id="run-1",
        evaluated_at=NOW,
    )
    rendered = " ".join(
        [run.rule.name, run.rule.description]
        + [result.explanation for result in run.results]
        + [reason for result in run.results for reason in result.exclusion_reasons]
    ).lower()

    assert not any(term in rendered for term in forbidden_signal_terms())


def _rule() -> ScreenerRule:
    return ScreenerRule(
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
                condition_id="market-cap-exists",
                field_name="market_cap",
                operator="exists",
                missing_behavior="exclude",
            ),
            ScreenerCondition(
                condition_id="roe-exists",
                field_name="roe",
                operator="exists",
                missing_behavior="exclude",
            ),
        ],
    )


def _candidate(
    symbol: str,
    *,
    lifecycle_status: str = "active",
    ohlcv_available: bool = True,
    freshness_state: str = "fresh",
    tier_input_fundamentals: str | None = "complete",
    fields: dict[str, object] | None = None,
    required_fields: list[str] | None = None,
) -> ScreenerCandidate:
    data_fields = fields if fields is not None else {"market_cap": 1_000_000, "roe": 0.18}
    required = required_fields if required_fields is not None else ["market_cap", "roe"]
    lifecycle = classify_ticker_coverage(
        symbol=symbol,
        lifecycle_status=cast(LifecycleStatus, lifecycle_status),
        ohlcv_available=ohlcv_available,
        ohlcv_freshness_state=cast(FreshnessState, freshness_state),
        provider_health_visible=True,
        fundamental_completeness=cast(CompletenessState | None, tier_input_fundamentals),
        source="manual",
        checked_at=NOW,
    )
    source = SourceCoverageSnapshot(
        symbol=symbol,
        provider_name="yfinance",
        source_type="ohlcv",
        provider_trust_tier="tier_3",
        availability_state="available" if ohlcv_available else "missing",
        freshness_state=cast(FreshnessState, freshness_state),
        last_checked_at=NOW,
    )
    fundamental = build_fundamental_snapshot(
        symbol=symbol,
        period="2026Q1",
        source="manual",
        source_type="manual",
        data_fields=data_fields,
        required_fields=required,
        coverage_tier=lifecycle.coverage_tier,
        freshness_state=cast(FreshnessState, freshness_state),
        provider_trust_tier="tier_3",
        fetched_at=NOW,
        imported_at=NOW,
    )
    return ScreenerCandidate(
        symbol=symbol,
        coverage=lifecycle,
        source_coverage=[source],
        fundamental=fundamental,
    )
