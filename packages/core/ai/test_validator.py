"""Validator: schema + banned phrases + invariants."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from packages.core.ai.validator import (
    ValidationError,
    count_sentences,
    scan_banned,
    validate_news_summary,
)
from packages.core.news.models import NewsSummary


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "news_id": 1,
        "url": "https://x.com/a",
        "summary": "Ringkasan singkat. Hanya dua kalimat.",
        "affected_tickers": ["BBCA.JK"],
        "sentiment_label": "neutral",
        "caveats": [],
        "source_quality": "reputable_media",
        "confidence": 0.85,
        "not_financial_advice": True,
        "prompt_template_id": "news_summary.v1",
        "model": "claude-haiku-4-5-20251001",
        "summarized_at": datetime(2026, 5, 18, tzinfo=UTC),
    }
    base.update(overrides)
    return base


def test_valid_payload_returns_parsed_model() -> None:
    parsed = validate_news_summary(_payload(), NewsSummary)
    assert isinstance(parsed, NewsSummary)


def test_banned_phrase_buy_now_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_news_summary(_payload(summary="Strong buy now untuk BBCA."), NewsSummary)
    assert exc.value.reason == "banned_phrase"


def test_banned_phrase_akan_naik_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_news_summary(_payload(summary="Saham BBCA akan naik bulan depan."), NewsSummary)
    assert exc.value.reason == "banned_phrase"


def test_banned_phrase_guaranteed_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_news_summary(_payload(summary="Guaranteed profit dari trade ini."), NewsSummary)
    assert exc.value.reason == "banned_phrase"


def test_banned_phrase_in_caveat_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_news_summary(
            _payload(summary="Berita netral.", caveats=["This is safe to ignore."]),
            NewsSummary,
        )
    assert exc.value.reason == "banned_phrase"


def test_target_price_banned() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_news_summary(_payload(summary="Target price BBCA Rp 12000."), NewsSummary)
    assert exc.value.reason == "banned_phrase"


def test_not_financial_advice_must_be_true() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_news_summary(_payload(not_financial_advice=False), NewsSummary)
    # pydantic schema may reject before invariant check — both acceptable
    assert exc.value.reason in {"schema", "not_financial_advice"}


def test_low_confidence_empty_caveats_rejected_by_pydantic() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_news_summary(_payload(confidence=0.4, caveats=[]), NewsSummary)
    assert exc.value.reason in {"schema", "empty_caveats"}


def test_summary_more_than_three_sentences_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_news_summary(
            _payload(summary="Satu. Dua. Tiga. Empat kalimat penuh."), NewsSummary
        )
    assert exc.value.reason == "summary_too_long"


def test_scan_banned_returns_none_for_clean_text() -> None:
    assert scan_banned("Berita netral biasa.") is None


def test_count_sentences_handles_question_and_exclaim() -> None:
    assert count_sentences("Satu. Dua! Tiga? Empat") == 4
