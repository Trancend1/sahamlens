"""Manual-first earnings event and summary models for V1-S6."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from typing import Any, Literal, Self

from packages.core.data_sources.normalize import normalize_ticker
from pydantic import BaseModel, Field, field_validator, model_validator

EarningsSourceType = Literal["manual", "local_note", "imported_file", "unknown"]
EarningsEventStatus = Literal["planned", "reported", "summarized", "archived"]
EarningsConfidenceStatus = Literal[
    "manual_only",
    "partial_local_data",
    "insufficient_data",
]

FORBIDDEN_EARNINGS_TERMS: tuple[str, ...] = (
    "buy",
    "sell",
    "profit opportunity",
    "strong upside",
    "guaranteed",
    "this stock will",
    "recommended action",
    "ai predicts",
)


class EarningsEventInput(BaseModel):
    ticker: str
    period: str
    event_date: date
    source_type: EarningsSourceType = "manual"
    source_ref: str | None = None
    notes: str | None = None
    now: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("ticker")
    @classmethod
    def _ticker_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ticker is required")
        return normalize_ticker(cleaned)

    @field_validator("period")
    @classmethod
    def _period_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("period is required")
        return cleaned

    @field_validator("source_ref", "notes")
    @classmethod
    def _blank_as_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def _safe_notes(self) -> Self:
        if self.notes:
            _ensure_safe_text(self.notes)
        return self


class EarningsEvent(BaseModel):
    id: str
    ticker: str
    period: str
    event_date: date
    source_type: EarningsSourceType
    source_ref: str | None = None
    status: EarningsEventStatus
    created_at: datetime
    updated_at: datetime
    notes: str | None = None

    @field_validator("ticker")
    @classmethod
    def _canon(cls, value: str) -> str:
        return normalize_ticker(value)


class EarningsSummary(BaseModel):
    id: str
    earnings_event_id: str
    generated_at: datetime
    summary_text: str
    caveats: list[str] = Field(default_factory=list)
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    confidence_status: EarningsConfidenceStatus

    @model_validator(mode="after")
    def _must_include_caveats_and_safe_text(self) -> Self:
        if not self.caveats:
            raise ValueError("summary must include caveats")
        _ensure_safe_text(self.summary_text)
        for caveat in self.caveats:
            _ensure_safe_text(caveat)
        return self


def validate_summary_notes(notes: str | None) -> str:
    cleaned = (notes or "").strip()
    if len(cleaned) < 40:
        raise ValueError("insufficient_data: add manual notes before generating a summary")
    _ensure_safe_text(cleaned)
    return cleaned


def _ensure_safe_text(value: str) -> None:
    lowered = value.lower()
    for term in FORBIDDEN_EARNINGS_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            raise ValueError(f"unsafe earnings text contains forbidden term: {term}")
