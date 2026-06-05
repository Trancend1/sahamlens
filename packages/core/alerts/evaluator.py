"""Manual local alert evaluation for V1-S6."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import duckdb
from packages.core.alerts.models import (
    ALLOWED_CONFIDENCE_FOR_ALERTS,
    ALLOWED_FRESHNESS_FOR_ALERTS,
    AlertEvaluation,
    AlertEvaluationInput,
    AlertEvaluationResult,
    AlertEvaluationStatus,
    AlertEvent,
    AlertRule,
    threshold_value,
)
from packages.core.alerts.repo import (
    insert_alert_evaluation,
    insert_alert_event,
    list_alert_rules,
)
from packages.core.fundamentals import get_latest_fundamental_snapshot
from packages.core.schemas.repository import load_ohlcv
from packages.core.ticker_coverage import list_source_coverage_snapshots


def evaluate_active_alert_rules(
    conn: duckdb.DuckDBPyConnection,
    *,
    evaluated_at: datetime | None = None,
) -> AlertEvaluationResult:
    timestamp = evaluated_at or datetime.now(UTC)
    evaluations: list[AlertEvaluation] = []
    events: list[AlertEvent] = []
    rules = list_alert_rules(conn, active_only=True, include_archived=False)
    for rule in rules:
        evaluation_input = _build_evaluation_input(conn, rule, evaluated_at=timestamp)
        evaluation, event = evaluate_alert_rule(evaluation_input)
        insert_alert_evaluation(conn, evaluation)
        evaluations.append(evaluation)
        if event is not None:
            insert_alert_event(conn, event)
            events.append(event)
    return AlertEvaluationResult(
        evaluated_count=len(evaluations),
        event_count=len(events),
        evaluations=evaluations,
        events=events,
    )


def evaluate_alert_rule(
    evaluation_input: AlertEvaluationInput,
) -> tuple[AlertEvaluation, AlertEvent | None]:
    rule = evaluation_input.rule
    evaluation_id = f"alert-eval-{uuid4().hex}"
    details = {
        "rule_type": rule.rule_type,
        "threshold": threshold_value(rule),
        "latest_close": evaluation_input.latest_close,
        "latest_volume": evaluation_input.latest_volume,
    }
    if evaluation_input.data_freshness_status not in ALLOWED_FRESHNESS_FOR_ALERTS:
        return (
            AlertEvaluation(
                id=evaluation_id,
                rule_id=rule.id,
                ticker=rule.ticker,
                evaluated_at=evaluation_input.evaluated_at,
                status="skipped_stale_data",
                reason=f"OHLCV freshness is {evaluation_input.data_freshness_status}.",
                data_freshness_status=evaluation_input.data_freshness_status,
                confidence_status=evaluation_input.confidence_status,
                matched=False,
                details=details,
            ),
            None,
        )
    if evaluation_input.confidence_status not in ALLOWED_CONFIDENCE_FOR_ALERTS:
        return (
            AlertEvaluation(
                id=evaluation_id,
                rule_id=rule.id,
                ticker=rule.ticker,
                evaluated_at=evaluation_input.evaluated_at,
                status="skipped_low_confidence",
                reason=f"Confidence is {evaluation_input.confidence_status}.",
                data_freshness_status=evaluation_input.data_freshness_status,
                confidence_status=evaluation_input.confidence_status,
                matched=False,
                details=details,
            ),
            None,
        )

    value = _rule_value(rule, evaluation_input)
    if value is None:
        return (
            AlertEvaluation(
                id=evaluation_id,
                rule_id=rule.id,
                ticker=rule.ticker,
                evaluated_at=evaluation_input.evaluated_at,
                status="failed_provider",
                reason="Required local price or volume data is unavailable.",
                data_freshness_status=evaluation_input.data_freshness_status,
                confidence_status=evaluation_input.confidence_status,
                matched=False,
                details=details,
            ),
            None,
        )

    threshold = threshold_value(rule)
    matched = _matches(rule, value, threshold)
    status: AlertEvaluationStatus = "success" if matched else "no_match"
    reason = (
        f"Rule condition matched with value {value:g} and threshold {threshold:g}."
        if matched
        else f"Rule condition did not match with value {value:g} and threshold {threshold:g}."
    )
    evaluation = AlertEvaluation(
        id=evaluation_id,
        rule_id=rule.id,
        ticker=rule.ticker,
        evaluated_at=evaluation_input.evaluated_at,
        status=status,
        reason=reason,
        data_freshness_status=evaluation_input.data_freshness_status,
        confidence_status=evaluation_input.confidence_status,
        matched=matched,
        details={**details, "value": value},
    )
    if not matched:
        return evaluation, None
    return evaluation, _build_event(rule, evaluation, value=value, threshold=threshold)


def _build_evaluation_input(
    conn: duckdb.DuckDBPyConnection,
    rule: AlertRule,
    *,
    evaluated_at: datetime,
) -> AlertEvaluationInput:
    latest = load_ohlcv(conn, rule.ticker, limit=1)
    latest_price = latest[-1] if latest else None
    source_coverage = list_source_coverage_snapshots(conn, symbol=rule.ticker)
    ohlcv_sources = [source for source in source_coverage if source.source_type == "ohlcv"]
    freshness = ohlcv_sources[0].freshness_state if ohlcv_sources else "unknown"
    fundamental = get_latest_fundamental_snapshot(conn, rule.ticker)
    confidence = fundamental.confidence_level if fundamental else "none"
    return AlertEvaluationInput(
        rule=rule,
        latest_close=latest_price["close"] if latest_price else None,
        latest_volume=latest_price["volume"] if latest_price else None,
        data_freshness_status=freshness,
        confidence_status=confidence,
        evaluated_at=evaluated_at,
    )


def _rule_value(rule: AlertRule, evaluation_input: AlertEvaluationInput) -> float | None:
    if rule.rule_type in {"price_above", "price_below"}:
        return evaluation_input.latest_close
    if rule.rule_type == "volume_above":
        return float(evaluation_input.latest_volume) if evaluation_input.latest_volume else None
    return None


def _matches(rule: AlertRule, value: float, threshold: float) -> bool:
    if rule.rule_type == "price_above":
        return value > threshold
    if rule.rule_type == "price_below":
        return value < threshold
    if rule.rule_type == "volume_above":
        return value > threshold
    return False


def _build_event(
    rule: AlertRule,
    evaluation: AlertEvaluation,
    *,
    value: float,
    threshold: float,
) -> AlertEvent:
    return AlertEvent(
        id=f"alert-event-{uuid4().hex}",
        rule_id=rule.id,
        evaluation_id=evaluation.id,
        ticker=rule.ticker,
        event_type=rule.rule_type,
        severity="info",
        title="Rule condition matched",
        message=(
            f"{rule.ticker} matched {rule.rule_type} with value {value:g} "
            f"and threshold {threshold:g}. Review freshness and confidence before acting."
        ),
        status="new",
        created_at=evaluation.evaluated_at,
    )
