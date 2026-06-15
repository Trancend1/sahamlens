"""Tests for policy gate: intent blocking, outbound scan, write confirmation."""

from __future__ import annotations

from services.hermes.intents import Intent
from services.hermes.policy import (
    check_intent_allowed,
    check_outbound_text,
    require_confirmation,
)


def test_all_read_intents_allowed() -> None:
    for intent in (
        Intent.BRIEF,
        Intent.TICKER_SNAPSHOT,
        Intent.EXPOSURE,
        Intent.JOURNAL_DIGEST,
        Intent.HELP,
    ):
        decision = check_intent_allowed(intent)
        assert decision.allowed is True, f"{intent} should be allowed"
        assert decision.requires_confirmation is False, f"{intent} should not require confirmation"


def test_write_intents_need_confirmation() -> None:
    for intent in (Intent.ALERT_TRIAGE, Intent.JOURNAL_CAPTURE, Intent.RESEARCH_ADD):
        decision = check_intent_allowed(intent)
        assert decision.allowed is True
        assert decision.requires_confirmation is True


def test_unknown_allowed_readonly() -> None:
    decision = check_intent_allowed(Intent.UNKNOWN)
    assert decision.allowed is True
    assert decision.requires_confirmation is False


def test_require_confirmation_helper() -> None:
    assert require_confirmation(Intent.JOURNAL_CAPTURE) is True
    assert require_confirmation(Intent.RESEARCH_ADD) is True
    assert require_confirmation(Intent.ALERT_TRIAGE) is True
    assert require_confirmation(Intent.BRIEF) is False
    assert require_confirmation(Intent.EXPOSURE) is False
    assert require_confirmation(Intent.HELP) is False


def test_outbound_clean_text_passes() -> None:
    decision = check_outbound_text("This is a normal research output.")
    assert decision.allowed is True
    assert decision.banned_hit is None


def test_outbound_banned_phrase_blocked() -> None:
    decision = check_outbound_text("Stock ini akan naik.")
    assert decision.allowed is False
    assert decision.banned_hit is not None


def test_outbound_target_price_blocked() -> None:
    decision = check_outbound_text("The target price is 5000.")
    assert decision.allowed is False


def test_outbound_dijamin_blocked() -> None:
    decision = check_outbound_text("Ini pasti untung, dijamin!")
    assert decision.allowed is False


def test_outbound_empty_text_passes() -> None:
    decision = check_outbound_text("")
    assert decision.allowed is True


def test_reason_present_on_block() -> None:
    decision = check_outbound_text("strong buy now")
    assert decision.allowed is False
    assert len(decision.reason) > 0
