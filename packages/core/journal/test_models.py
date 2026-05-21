"""Validation tests for journal Pydantic models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from packages.core.journal.models import CritiqueCheck, JournalCritique, TradePlan
from pydantic import ValidationError


def _plan(**kwargs: object) -> TradePlan:
    defaults: dict[str, object] = {
        "id": 1_000_000,
        "symbol": "BBCA.JK",
        "setup_type": "breakout",
        "thesis": "Harga menembus resistance kunci",
        "entry_plan": "Beli saat harga tutup di atas 9500",
        "stop_level": 9200.0,
        "invalidation": "Tutup harian di bawah 9200",
        "target": "10200",
        "position_size_rupiah": 10_000_000,
        "max_loss_rupiah": 300_000,
        "created_at": datetime(2026, 5, 21, tzinfo=UTC),
    }
    defaults.update(kwargs)
    return TradePlan.model_validate(defaults)


def test_valid_plan_creates_successfully() -> None:
    plan = _plan()
    assert plan.symbol == "BBCA.JK"
    assert plan.status == "planned"


def test_symbol_normalized_to_uppercase_dot_jk() -> None:
    plan = _plan(symbol="bbca")
    assert plan.symbol == "BBCA.JK"


def test_invalid_setup_type_raises() -> None:
    with pytest.raises(ValidationError):
        _plan(setup_type="unknown_type")


def test_invalid_status_raises() -> None:
    with pytest.raises(ValidationError):
        _plan(status="pending")


def test_invalid_emotion_raises() -> None:
    with pytest.raises(ValidationError):
        _plan(emotion="happy")


def test_emotion_none_is_allowed() -> None:
    plan = _plan(emotion=None)
    assert plan.emotion is None


def test_valid_emotion_values() -> None:
    for emotion in ("calm", "excited", "fearful", "greedy", "uncertain"):
        plan = _plan(emotion=emotion)
        assert plan.emotion == emotion


def test_result_and_lesson_optional() -> None:
    plan = _plan()
    assert plan.result_rupiah is None
    assert plan.lesson is None


def test_reviewed_at_optional() -> None:
    plan = _plan()
    assert plan.reviewed_at is None


def test_missing_required_field_raises() -> None:
    with pytest.raises(ValidationError):
        TradePlan.model_validate({"id": 1, "symbol": "BBCA.JK"})


def test_journal_critique_valid() -> None:
    critique = JournalCritique(
        plan_id=1_000_000,
        checks=[
            CritiqueCheck(
                category="thesis",
                status="ok",
                finding="Thesis jelas",
                suggested_question="Apa katalis utama?",
            )
        ],
        overall_risk_flag="green",
        caveats=["Verifikasi data fundamental"],
        not_financial_advice=True,
    )
    assert critique.not_financial_advice is True
    assert len(critique.checks) == 1


def test_critique_invalid_flag_raises() -> None:
    with pytest.raises(ValidationError):
        JournalCritique(
            plan_id=1,
            checks=[],
            overall_risk_flag="approve",  # type: ignore[arg-type]
            caveats=[],
        )


def test_critique_no_approval_field() -> None:
    critique = JournalCritique(plan_id=1, checks=[], overall_risk_flag="incomplete", caveats=[])
    assert not hasattr(critique, "approval")
