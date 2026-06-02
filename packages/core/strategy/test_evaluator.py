from __future__ import annotations

from datetime import UTC, datetime

from packages.core.journal.models import TradePlan
from packages.core.strategy import (
    StrategyRule,
    default_strategy_rules,
    evaluate_strategy_rules,
    forbidden_strategy_signal_terms,
)

NOW = datetime(2026, 6, 2, 10, 0, tzinfo=UTC)


def test_default_strategy_rules_pass_for_complete_plan() -> None:
    evaluations = evaluate_strategy_rules(
        _complete_plan(),
        default_strategy_rules(now=NOW),
        evaluated_at=NOW,
        review_id="review-1",
    )

    assert {evaluation.evaluation_status for evaluation in evaluations} == {"pass"}
    assert all(evaluation.evidence for evaluation in evaluations)
    assert all(evaluation.violations == [] for evaluation in evaluations)


def test_strategy_rules_fail_with_explicit_violation_when_named_check_is_missing() -> None:
    plan = _complete_plan(stop_level=0.0, invalidation="", emotion=None)

    evaluations = evaluate_strategy_rules(
        plan,
        default_strategy_rules(now=NOW),
        evaluated_at=NOW,
        review_id="review-1",
    )

    failed = {
        evaluation.rule_id: evaluation
        for evaluation in evaluations
        if evaluation.evaluation_status == "fail"
    }
    assert "stop_loss_present" in failed
    assert "invalidation_present" in failed
    assert "emotion_logged" in failed
    assert failed["stop_loss_present"].violations[0].violation_code == "missing_stop_loss"
    assert "stop_level" in failed["stop_loss_present"].violations[0].violation_detail


def test_strategy_rules_return_needs_data_for_unknown_required_fields() -> None:
    custom = StrategyRule(
        rule_id="unknown_required_field",
        name="Unknown required field",
        description="Requires a field that old journal rows do not expose.",
        rule_category="review_hygiene",
        required_fields=["unmapped_field"],
        violation_code="missing_unmapped_field",
        created_at=NOW,
        updated_at=NOW,
    )

    evaluation = evaluate_strategy_rules(
        _complete_plan(),
        [custom],
        evaluated_at=NOW,
        review_id="review-1",
    )[0]

    assert evaluation.evaluation_status == "needs_data"
    assert evaluation.violations == []
    assert "unmapped_field" in evaluation.reason
    assert evaluation.caveats


def test_strategy_rule_copy_avoids_signal_terms() -> None:
    evaluations = evaluate_strategy_rules(
        _complete_plan(stop_level=0.0),
        default_strategy_rules(now=NOW),
        evaluated_at=NOW,
        review_id="review-1",
    )
    rendered = " ".join(
        [evaluation.reason for evaluation in evaluations]
        + [
            violation.violation_detail
            for evaluation in evaluations
            for violation in evaluation.violations
        ]
    ).lower()

    assert not any(term in rendered for term in forbidden_strategy_signal_terms())


def _complete_plan(**overrides: object) -> TradePlan:
    data: dict[str, object] = {
        "id": 1,
        "symbol": "BBCA",
        "setup_type": "breakout",
        "thesis": "Breakout with visible volume support.",
        "entry_plan": "Review entry only after close above resistance.",
        "stop_level": 9100.0,
        "invalidation": "Close below prior support.",
        "target": "Prior swing high.",
        "position_size_rupiah": 10_000_000,
        "max_loss_rupiah": 250_000,
        "emotion": "calm",
        "status": "planned",
        "created_at": NOW,
    }
    data.update(overrides)
    return TradePlan.model_validate(data)
