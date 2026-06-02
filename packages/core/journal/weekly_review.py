"""Weekly journal review generator for behavior reflection."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

from packages.core.journal.models import (
    TradePlan,
    WeeklyFindingSeverity,
    WeeklyFindingType,
    WeeklyReviewFinding,
    WeeklyReviewRun,
)
from packages.core.strategy import StrategyRule, evaluate_strategy_rules
from packages.core.strategy.models import StrategyRuleEvaluation


def generate_weekly_journal_review(
    plans: list[TradePlan],
    rules: list[StrategyRule],
    *,
    review_id: str,
    period_start: datetime,
    period_end: datetime,
    generated_at: datetime,
) -> WeeklyReviewRun:
    scoped_plans = [
        plan for plan in plans if period_start <= _normalize_datetime(plan.created_at) <= period_end
    ]
    evaluations = [
        evaluation
        for plan in scoped_plans
        for evaluation in evaluate_strategy_rules(
            plan,
            rules,
            evaluated_at=generated_at,
            review_id=review_id,
        )
    ]
    violations = [violation for evaluation in evaluations for violation in evaluation.violations]
    needs_data_count = sum(
        1 for evaluation in evaluations if evaluation.evaluation_status == "needs_data"
    )
    findings = _build_findings(
        review_id=review_id,
        plans=scoped_plans,
        evaluations=evaluations,
        generated_at=generated_at,
    )
    caveats = _caveats(scoped_plans, needs_data_count)
    return WeeklyReviewRun(
        review_id=review_id,
        period_start=period_start,
        period_end=period_end,
        generated_at=generated_at,
        status="completed",
        journal_entry_count=len(scoped_plans),
        reviewed_plan_count=len(scoped_plans),
        rule_evaluation_count=len(evaluations),
        violation_count=len(violations),
        needs_data_count=needs_data_count,
        summary=_summary(scoped_plans, evaluations, len(violations), needs_data_count),
        evidence=_evidence(scoped_plans, evaluations),
        caveats=caveats,
        findings=findings,
        rule_evaluations=evaluations,
    )


def _build_findings(
    *,
    review_id: str,
    plans: list[TradePlan],
    evaluations: list[StrategyRuleEvaluation],
    generated_at: datetime,
) -> list[WeeklyReviewFinding]:
    if not plans:
        return [
            _finding(
                review_id=review_id,
                finding_type="missing_data",
                title="No journal entries",
                detail="No journal entries were found for this weekly review period.",
                severity="warning",
                evidence=[],
                caveats=["Weekly review quality depends on journal entries."],
                created_at=generated_at,
            )
        ]

    findings: list[WeeklyReviewFinding] = []
    status_counts = Counter(plan.status for plan in plans)
    findings.append(
        _finding(
            review_id=review_id,
            finding_type="behavior_pattern",
            title="Plan status mix",
            detail=", ".join(
                f"{status}: {count}" for status, count in sorted(status_counts.items())
            ),
            severity="info",
            evidence=[f"{len(plans)} journal entries in review period."],
            caveats=["Status mix is descriptive, not a performance judgement."],
            created_at=generated_at,
        )
    )

    violation_counts = Counter(
        violation.violation_code
        for evaluation in evaluations
        for violation in evaluation.violations
    )
    for code, count in sorted(violation_counts.items()):
        related = [
            violation.violation_detail
            for evaluation in evaluations
            for violation in evaluation.violations
            if violation.violation_code == code
        ]
        findings.append(
            _finding(
                review_id=review_id,
                finding_type="rule_violation",
                title=f"{code} repeated {count} time(s)",
                detail=f"{code}: {' | '.join(related)}",
                severity="warning",
                evidence=related,
                caveats=["Rule violations are journal hygiene checks, not trade signals."],
                created_at=generated_at,
            )
        )

    missing_lessons = [
        plan
        for plan in plans
        if plan.status in {"closed", "skipped"} and not (plan.lesson or "").strip()
    ]
    if missing_lessons:
        findings.append(
            _finding(
                review_id=review_id,
                finding_type="follow_up",
                title="Closed or skipped plans need lessons",
                detail=f"{len(missing_lessons)} closed/skipped plan(s) have no lesson recorded.",
                severity="warning",
                evidence=[f"{plan.symbol} journal {plan.id}" for plan in missing_lessons],
                caveats=["Follow-up prompts support reflection only."],
                created_at=generated_at,
            )
        )

    return findings


def _summary(
    plans: list[TradePlan],
    evaluations: list[StrategyRuleEvaluation],
    violation_count: int,
    needs_data_count: int,
) -> str:
    return (
        "Weekly review: "
        f"{len(plans)} journal plan(s), "
        f"{len(evaluations)} rule evaluation(s), "
        f"{violation_count} violation(s), "
        f"{needs_data_count} needs-data result(s)."
    )


def _evidence(
    plans: list[TradePlan],
    evaluations: list[StrategyRuleEvaluation],
) -> list[str]:
    evidence = [f"{plan.symbol} journal {plan.id} status {plan.status}" for plan in plans]
    evidence.extend(
        f"{evaluation.rule_id}: {evaluation.evaluation_status}" for evaluation in evaluations[:10]
    )
    return evidence


def _caveats(plans: list[TradePlan], needs_data_count: int) -> list[str]:
    caveats = [
        "Weekly review is behavior reflection only and is not financial advice.",
        "Review quality depends on complete local journal entries.",
    ]
    if not plans:
        caveats.append("No journal entries were available for this period.")
    if needs_data_count:
        caveats.append(f"{needs_data_count} rule evaluation(s) need more journal data.")
    return caveats


def _finding(
    *,
    review_id: str,
    finding_type: WeeklyFindingType,
    title: str,
    detail: str,
    severity: WeeklyFindingSeverity,
    evidence: list[str],
    caveats: list[str],
    created_at: datetime,
) -> WeeklyReviewFinding:
    return WeeklyReviewFinding.model_validate(
        {
            "finding_id": f"weekly-finding-{uuid4().hex}",
            "review_id": review_id,
            "finding_type": finding_type,
            "title": title,
            "detail": detail,
            "severity": severity,
            "evidence": evidence,
            "caveats": caveats,
            "created_at": created_at,
        }
    )


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
