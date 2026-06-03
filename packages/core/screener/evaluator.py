"""Transparent screener evaluator for V1-S3."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from packages.core.fundamentals.models import CompletenessState, ConfidenceLevel
from packages.core.screener.models import (
    ResultStatus,
    ScreenerCandidate,
    ScreenerCondition,
    ScreenerExclusion,
    ScreenerResult,
    ScreenerRule,
    ScreenerRun,
)
from packages.core.ticker_coverage.models import CoverageTier, LifecycleStatus

_COVERAGE_RANK: dict[CoverageTier, int] = {"tier_c": 1, "tier_b": 2, "tier_a": 3}
_COMPLETENESS_RANK: dict[CompletenessState, int] = {
    "missing": 1,
    "sparse": 2,
    "partial": 3,
    "complete": 4,
}
_CONFIDENCE_RANK: dict[ConfidenceLevel, int] = {
    "none": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
}


def evaluate_screener_rule(
    rule: ScreenerRule,
    candidates: list[ScreenerCandidate],
    *,
    run_id: str,
    evaluated_at: datetime,
    data_quality_snapshot: dict[str, Any] | None = None,
) -> ScreenerRun:
    results = [
        _evaluate_candidate(rule, candidate, run_id=run_id, evaluated_at=evaluated_at)
        for candidate in candidates
    ]
    included_count = sum(1 for result in results if result.result_status == "included")
    return ScreenerRun(
        run_id=run_id,
        rule=rule,
        started_at=evaluated_at,
        completed_at=evaluated_at,
        status="completed",
        universe_count=len(candidates),
        included_count=included_count,
        excluded_count=len(candidates) - included_count,
        data_quality_snapshot=data_quality_snapshot or {},
        results=results,
    )


def _evaluate_candidate(
    rule: ScreenerRule,
    candidate: ScreenerCandidate,
    *,
    run_id: str,
    evaluated_at: datetime,
) -> ScreenerResult:
    exclusions: list[ScreenerExclusion] = []
    caveats: list[str] = []
    missing_fields: list[str] = []
    matched_conditions: list[str] = []
    failed_conditions: list[str] = []

    coverage_tier: CoverageTier = (
        candidate.coverage.coverage_tier if candidate.coverage else "tier_c"
    )
    lifecycle_status: LifecycleStatus = (
        candidate.coverage.lifecycle_status if candidate.coverage else "unknown"
    )
    freshness_state = candidate.freshness_state
    completeness_state = candidate.fundamental.completeness_state if candidate.fundamental else None
    confidence_level = candidate.fundamental.confidence_level if candidate.fundamental else None

    if candidate.coverage is None:
        exclusions.append(_exclusion("missing_coverage", "missing coverage snapshot", "coverage"))
    elif not candidate.coverage.screener_eligible:
        detail = candidate.coverage.eligibility_reason or "ticker is not screener eligible"
        exclusions.append(
            _exclusion("ticker_ineligible", f"ticker ineligible: {detail}", "coverage")
        )

    if lifecycle_status != "active":
        exclusions.append(
            _exclusion(
                "lifecycle_restricted",
                f"lifecycle {lifecycle_status} is excluded",
                "lifecycle_status",
            )
        )

    if _COVERAGE_RANK[coverage_tier] < _COVERAGE_RANK[rule.min_coverage_tier]:
        exclusions.append(
            _exclusion(
                "coverage_tier_below_minimum",
                f"coverage tier {coverage_tier} below rule minimum {rule.min_coverage_tier}",
                "coverage_tier",
            )
        )

    if freshness_state not in rule.allowed_freshness_states:
        exclusions.append(
            _exclusion(
                "freshness_not_allowed",
                f"freshness {freshness_state} is not allowed for this filter",
                "freshness_state",
            )
        )

    if rule.min_fundamental_completeness:
        if completeness_state is None:
            exclusions.append(
                _exclusion("missing_fundamentals", "missing fundamental snapshot", "fundamentals")
            )
        elif (
            _COMPLETENESS_RANK[completeness_state]
            < _COMPLETENESS_RANK[rule.min_fundamental_completeness]
        ):
            exclusions.append(
                _exclusion(
                    "fundamental_completeness_below_minimum",
                    (
                        f"fundamental completeness {completeness_state} below "
                        f"{rule.min_fundamental_completeness}"
                    ),
                    "completeness_state",
                )
            )

    if rule.min_confidence_level:
        if confidence_level is None:
            exclusions.append(
                _exclusion("missing_confidence", "missing confidence level", "confidence")
            )
        elif _CONFIDENCE_RANK[confidence_level] < _CONFIDENCE_RANK[rule.min_confidence_level]:
            exclusions.append(
                _exclusion(
                    "confidence_below_minimum",
                    f"confidence {confidence_level} below {rule.min_confidence_level}",
                    "confidence_level",
                )
            )

    for field in rule.required_fields:
        if candidate.resolve_field(field) is None and field not in missing_fields:
            missing_fields.append(field)
            exclusions.append(
                _exclusion("missing_required_field", f"missing required field {field}", field)
            )

    for condition in rule.conditions:
        outcome = _evaluate_condition(condition, candidate)
        if outcome == "matched":
            matched_conditions.append(condition.label)
            continue
        if outcome == "missing":
            if condition.field_name not in missing_fields:
                missing_fields.append(condition.field_name)
            if condition.missing_behavior == "caveat":
                caveats.append(f"missing field {condition.field_name}; condition treated as caveat")
            else:
                failed_conditions.append(condition.label)
                exclusions.append(
                    _exclusion(
                        "missing_condition_field",
                        f"missing required field {condition.field_name}",
                        condition.field_name,
                    )
                )
            continue
        failed_conditions.append(condition.label)
        exclusions.append(
            _exclusion(
                "condition_not_matched",
                f"condition not matched: {condition.label}",
                condition.field_name,
            )
        )

    if candidate.fundamental and candidate.fundamental.caveat:
        caveats.append(candidate.fundamental.caveat)

    status: ResultStatus = "excluded" if exclusions else "included"
    reasons = [exclusion.reason_detail for exclusion in exclusions]
    explanation = _explanation(rule, candidate.symbol, status=status, reasons=reasons)
    return ScreenerResult(
        run_id=run_id,
        symbol=candidate.symbol,
        result_status=status,
        coverage_tier=coverage_tier,
        lifecycle_status=lifecycle_status,
        freshness_state=freshness_state,
        completeness_state=completeness_state,
        confidence_level=confidence_level,
        matched_conditions=matched_conditions,
        failed_conditions=failed_conditions,
        missing_fields=missing_fields,
        exclusion_reasons=reasons,
        exclusions=exclusions,
        caveats=caveats,
        explanation=explanation,
        evaluated_at=evaluated_at,
    )


def _evaluate_condition(condition: ScreenerCondition, candidate: ScreenerCandidate) -> str:
    actual = candidate.resolve_field(condition.field_name)
    if actual is None:
        return "missing"
    if condition.operator == "exists":
        return "matched"
    if condition.operator == "eq":
        return "matched" if actual == condition.value else "failed"
    if condition.operator == "neq":
        return "matched" if actual != condition.value else "failed"
    if condition.operator in {"gt", "gte", "lt", "lte"}:
        if not isinstance(actual, int | float) or not isinstance(condition.value, int | float):
            return "failed"
        return (
            "matched" if _compare_number(actual, condition.operator, condition.value) else "failed"
        )
    if condition.operator == "between":
        if (
            not isinstance(actual, int | float)
            or not isinstance(condition.value, list)
            or len(condition.value) != 2
            or not all(isinstance(value, int | float) for value in condition.value)
        ):
            return "failed"
        return "matched" if condition.value[0] <= actual <= condition.value[1] else "failed"
    return "failed"


def _compare_number(actual: int | float, operator: str, expected: int | float) -> bool:
    if operator == "gt":
        return actual > expected
    if operator == "gte":
        return actual >= expected
    if operator == "lt":
        return actual < expected
    return actual <= expected


def _exclusion(reason_code: str, reason_detail: str, source_field: str | None) -> ScreenerExclusion:
    return ScreenerExclusion(
        reason_code=reason_code,
        reason_detail=reason_detail,
        source_field=source_field,
    )


def _explanation(
    rule: ScreenerRule,
    symbol: str,
    *,
    status: str,
    reasons: list[str],
) -> str:
    if status == "included":
        return f"{symbol} matched filter {rule.name}; review caveats before using this output."
    return f"{symbol} excluded from filter {rule.name}: {'; '.join(reasons)}."
