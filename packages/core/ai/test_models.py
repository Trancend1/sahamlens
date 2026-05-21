"""Tests for AI output Pydantic models."""

from __future__ import annotations

import pytest
from packages.core.ai.models import ChatResponse, EvidenceItem, StockBrief
from pydantic import ValidationError as PydanticValidationError


def _evidence() -> list[dict[str, object]]:
    return [
        {
            "type": "price",
            "value": "Close 9500",
            "source_ref": "price_history",
            "freshness": "2026-05-21",
        }
    ]


def _brief_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "symbol": "BBCA.JK",
        "analysis_date": "2026-05-21",
        "prompt_template_id": "stock_brief.v1",
        "model": "claude-sonnet-4-6",
        "evidence": _evidence(),
        "bullish_view": "MA 50 di bawah harga, RSI belum overbought.",
        "bearish_view": "Volume turun, berita negatif sektor.",
        "uncertainty": "Data fundamental tidak tersedia.",
        "caveats": ["Analisis berdasarkan indikator teknikal saja."],
        "beginner_explanation": "Harga naik dengan indikator netral.",
        "suggested_next_question": "Apakah ada katalis fundamental?",
        "not_financial_advice": True,
    }
    base.update(overrides)
    return base


def _chat_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "question": "Bagaimana tren RSI BBCA?",
        "answer": "RSI saat ini di 55, belum overbought.",
        "evidence": _evidence(),
        "caveats": ["RSI adalah indikator lagging."],
        "not_financial_advice": True,
    }
    base.update(overrides)
    return base


def test_stock_brief_valid() -> None:
    b = StockBrief.model_validate(_brief_payload())
    assert b.symbol == "BBCA.JK"
    assert b.not_financial_advice is True
    assert len(b.evidence) == 1
    assert b.evidence[0].type == "price"


def test_stock_brief_empty_evidence_rejected() -> None:
    with pytest.raises(PydanticValidationError):
        StockBrief.model_validate(_brief_payload(evidence=[]))


def test_stock_brief_empty_caveats_rejected() -> None:
    with pytest.raises(PydanticValidationError):
        StockBrief.model_validate(_brief_payload(caveats=[]))


def test_stock_brief_empty_uncertainty_rejected() -> None:
    with pytest.raises(PydanticValidationError):
        StockBrief.model_validate(_brief_payload(uncertainty=""))


def test_stock_brief_not_financial_advice_defaults_true() -> None:
    payload = _brief_payload()
    del payload["not_financial_advice"]
    b = StockBrief.model_validate(payload)
    assert b.not_financial_advice is True


def test_chat_response_valid() -> None:
    r = ChatResponse.model_validate(_chat_payload())
    assert r.question == "Bagaimana tren RSI BBCA?"
    assert r.not_financial_advice is True
    assert len(r.caveats) == 1


def test_chat_response_empty_caveats_rejected() -> None:
    with pytest.raises(PydanticValidationError):
        ChatResponse.model_validate(_chat_payload(caveats=[]))


def test_evidence_item_valid_types() -> None:
    for ev_type in ("price", "indicator", "news", "fundamental", "journal"):
        item = EvidenceItem.model_validate(
            {"type": ev_type, "value": "v", "source_ref": "r", "freshness": "2026-05-21"}
        )
        assert item.type == ev_type


def test_evidence_item_invalid_type_rejected() -> None:
    with pytest.raises(PydanticValidationError):
        EvidenceItem.model_validate(
            {"type": "unknown", "value": "v", "source_ref": "r", "freshness": "2026-05-21"}
        )
