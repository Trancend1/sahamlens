"""Pydantic models for AI output schemas.

Schemas mirror AI_BOUNDARIES.md §3.1 (analysis_output) and §3.2 (chat_response).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator

EvidenceType = Literal["price", "indicator", "news", "fundamental", "journal"]


class EvidenceItem(BaseModel):
    type: EvidenceType
    value: str
    source_ref: str
    freshness: str  # ISO 8601 datetime of underlying data


class StockBrief(BaseModel):
    """analysis_output schema — AI_BOUNDARIES.md §3.1."""

    symbol: str
    analysis_date: str  # ISO 8601
    prompt_template_id: str
    model: str
    evidence: list[EvidenceItem]
    bullish_view: str
    bearish_view: str
    uncertainty: str
    caveats: list[str]
    beginner_explanation: str
    suggested_next_question: str
    not_financial_advice: bool = True

    @field_validator("evidence")
    @classmethod
    def evidence_non_empty(cls, v: list[EvidenceItem]) -> list[EvidenceItem]:
        if not v:
            raise ValueError("evidence must not be empty")
        return v

    @field_validator("caveats")
    @classmethod
    def caveats_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("caveats must not be empty")
        return v

    @field_validator("uncertainty")
    @classmethod
    def uncertainty_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("uncertainty must not be empty")
        return v


class ChatResponse(BaseModel):
    """Conversational Q&A response with RAG context, not analysis_output full schema."""

    question: str
    answer: str
    evidence: list[EvidenceItem]
    caveats: list[str]
    not_financial_advice: bool = True

    @field_validator("caveats")
    @classmethod
    def caveats_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("caveats must not be empty")
        return v
