from __future__ import annotations

from datetime import UTC, datetime

from packages.core.journal.models import TradePlan
from packages.core.journal.weekly_review import generate_weekly_journal_review
from packages.core.strategy import default_strategy_rules

NOW = datetime(2026, 6, 2, 10, 0, tzinfo=UTC)
PERIOD_START = datetime(2026, 5, 25, tzinfo=UTC)
PERIOD_END = datetime(2026, 6, 1, 23, 59, tzinfo=UTC)


def test_weekly_review_summarizes_behavior_and_rule_violations() -> None:
    review = generate_weekly_journal_review(
        [_plan(1), _plan(2, stop_level=0.0, invalidation="", emotion=None)],
        default_strategy_rules(now=NOW),
        review_id="review-1",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        generated_at=NOW,
    )

    assert review.review_id == "review-1"
    assert review.status == "completed"
    assert review.journal_entry_count == 2
    assert review.violation_count >= 3
    assert review.summary.startswith("Weekly review")
    assert review.evidence
    assert review.caveats
    assert any(finding.finding_type == "rule_violation" for finding in review.findings)
    assert any("missing_stop_loss" in finding.detail for finding in review.findings)


def test_weekly_review_handles_empty_weeks_with_caveat() -> None:
    review = generate_weekly_journal_review(
        [],
        default_strategy_rules(now=NOW),
        review_id="review-empty",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        generated_at=NOW,
    )

    assert review.status == "completed"
    assert review.journal_entry_count == 0
    assert review.rule_evaluation_count == 0
    assert review.findings[0].finding_type == "missing_data"
    assert "No journal entries" in review.findings[0].detail
    assert review.caveats


def test_weekly_review_filters_entries_outside_period() -> None:
    out_of_period = _plan(2, created_at=datetime(2026, 5, 1, tzinfo=UTC))

    review = generate_weekly_journal_review(
        [_plan(1), out_of_period],
        default_strategy_rules(now=NOW),
        review_id="review-1",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        generated_at=NOW,
    )

    assert review.journal_entry_count == 1
    assert all(evaluation.journal_id == 1 for evaluation in review.rule_evaluations)


def _plan(plan_id: int, **overrides: object) -> TradePlan:
    data: dict[str, object] = {
        "id": plan_id,
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
        "created_at": datetime(2026, 5, 30, tzinfo=UTC),
    }
    data.update(overrides)
    return TradePlan.model_validate(data)
