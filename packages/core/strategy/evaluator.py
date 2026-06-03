"""Evaluate simple named strategy rules against journal plans."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from packages.core.journal.models import TradePlan
from packages.core.strategy.models import (
    StrategyEvaluationStatus,
    StrategyRule,
    StrategyRuleEvaluation,
    StrategyRuleViolation,
)

_KNOWN_FIELDS = {
    "symbol",
    "setup_type",
    "thesis",
    "entry_plan",
    "stop_level",
    "invalidation",
    "target",
    "position_size_rupiah",
    "max_loss_rupiah",
    "emotion",
    "status",
    "result_rupiah",
    "lesson",
    "created_at",
    "reviewed_at",
}


def default_strategy_rules(*, now: datetime | None = None) -> list[StrategyRule]:
    timestamp = now or datetime.now(UTC)
    return [
        StrategyRule(
            rule_id="thesis_present",
            name="Thesis present",
            description="Checks that each journal plan records a thesis.",
            rule_category="journal_completeness",
            required_fields=["thesis"],
            violation_code="missing_thesis",
            created_at=timestamp,
            updated_at=timestamp,
        ),
        StrategyRule(
            rule_id="planned_entry_present",
            name="Planned entry present",
            description="Checks that each journal plan records an entry plan.",
            rule_category="plan_adherence",
            required_fields=["entry_plan"],
            violation_code="missing_entry_plan",
            created_at=timestamp,
            updated_at=timestamp,
        ),
        StrategyRule(
            rule_id="stop_loss_present",
            name="Stop loss present",
            description="Checks that each journal plan records a stop level.",
            rule_category="risk_discipline",
            required_fields=["stop_level"],
            violation_code="missing_stop_loss",
            created_at=timestamp,
            updated_at=timestamp,
        ),
        StrategyRule(
            rule_id="risk_limit_present",
            name="Risk limit present",
            description="Checks that each journal plan records max loss and position size.",
            rule_category="risk_discipline",
            required_fields=["max_loss_rupiah", "position_size_rupiah"],
            violation_code="missing_risk_limit",
            created_at=timestamp,
            updated_at=timestamp,
        ),
        StrategyRule(
            rule_id="invalidation_present",
            name="Invalidation present",
            description="Checks that each journal plan records invalidation conditions.",
            rule_category="plan_adherence",
            required_fields=["invalidation"],
            violation_code="missing_invalidation",
            created_at=timestamp,
            updated_at=timestamp,
        ),
        StrategyRule(
            rule_id="emotion_logged",
            name="Emotion logged",
            description="Checks that each journal plan records the owner emotion state.",
            rule_category="emotion_discipline",
            required_fields=["emotion"],
            violation_code="missing_emotion",
            created_at=timestamp,
            updated_at=timestamp,
        ),
    ]


def evaluate_strategy_rules(
    plan: TradePlan,
    rules: list[StrategyRule],
    *,
    evaluated_at: datetime,
    review_id: str | None = None,
) -> list[StrategyRuleEvaluation]:
    return [
        _evaluate_rule(plan, rule, evaluated_at=evaluated_at, review_id=review_id) for rule in rules
    ]


def _evaluate_rule(
    plan: TradePlan,
    rule: StrategyRule,
    *,
    evaluated_at: datetime,
    review_id: str | None,
) -> StrategyRuleEvaluation:
    evaluation_id = f"strategy-eval-{uuid4().hex}"
    if not rule.is_active:
        return StrategyRuleEvaluation(
            evaluation_id=evaluation_id,
            review_id=review_id,
            rule_id=rule.rule_id,
            journal_id=plan.id,
            symbol=plan.symbol,
            evaluation_status="skipped",
            evaluated_at=evaluated_at,
            reason=f"{rule.name} skipped because rule is inactive.",
        )

    unknown_fields = [field for field in rule.required_fields if field not in _KNOWN_FIELDS]
    if unknown_fields:
        status: StrategyEvaluationStatus = (
            "skipped" if rule.needs_data_behavior == "skip" else "needs_data"
        )
        return StrategyRuleEvaluation(
            evaluation_id=evaluation_id,
            review_id=review_id,
            rule_id=rule.rule_id,
            journal_id=plan.id,
            symbol=plan.symbol,
            evaluation_status=status,
            evaluated_at=evaluated_at,
            caveats=[f"Rule requires unavailable fields: {', '.join(unknown_fields)}."],
            reason=f"{rule.name} needs data: {', '.join(unknown_fields)}.",
        )

    missing_fields = [
        field for field in rule.required_fields if not _has_value(_field(plan, field))
    ]
    if not missing_fields:
        return StrategyRuleEvaluation(
            evaluation_id=evaluation_id,
            review_id=review_id,
            rule_id=rule.rule_id,
            journal_id=plan.id,
            symbol=plan.symbol,
            evaluation_status="pass",
            evaluated_at=evaluated_at,
            evidence=[f"{plan.symbol} journal {plan.id} has {', '.join(rule.required_fields)}."],
            reason=f"{rule.name} passed for {plan.symbol}.",
        )

    detail = f"{plan.symbol} journal {plan.id} is missing {', '.join(missing_fields)}."
    violation = StrategyRuleViolation(
        violation_id=f"strategy-violation-{uuid4().hex}",
        evaluation_id=evaluation_id,
        review_id=review_id,
        rule_id=rule.rule_id,
        journal_id=plan.id,
        symbol=plan.symbol,
        violation_code=rule.violation_code,
        violation_detail=detail,
        evidence=[detail],
        caveats=["Treat this as a journal completeness check, not a trade signal."],
        created_at=evaluated_at,
    )
    return StrategyRuleEvaluation(
        evaluation_id=evaluation_id,
        review_id=review_id,
        rule_id=rule.rule_id,
        journal_id=plan.id,
        symbol=plan.symbol,
        evaluation_status="fail",
        evaluated_at=evaluated_at,
        evidence=[detail],
        caveats=["Rule failed because required journal fields were missing or empty."],
        reason=f"{rule.name} failed for {plan.symbol}: missing {', '.join(missing_fields)}.",
        violations=[violation],
    )


def _field(plan: TradePlan, field: str) -> Any | None:
    return getattr(plan, field, None)


def _has_value(value: Any | None) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, int | float):
        return value > 0
    return True
