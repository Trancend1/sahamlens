"""Output validator: schema parse + banned-phrase filter + invariants.

Banned phrases from AI_BOUNDARIES.md §4.4. Validator REJECTS malformed output;
caller may retry up to 3x per the same policy.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

ReasonCode = Literal[
    "banned_phrase",
    "schema",
    "empty_caveats",
    "empty_evidence",
    "empty_uncertainty",
    "not_financial_advice",
    "summary_too_long",
]

BANNED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(saham|stock).*akan\s+(naik|turun)", re.IGNORECASE | re.DOTALL),
    re.compile(r"guaranteed|pasti\s+untung|dijamin", re.IGNORECASE),
    re.compile(r"(strong\s+)?buy\s+now|sell\s+now|enter\s+now", re.IGNORECASE),
    re.compile(r"this\s+is\s+safe|aman\s+untuk\s+dibeli", re.IGNORECASE),
    re.compile(r"target\s+price", re.IGNORECASE),
)

MAX_SENTENCES = 3


class ValidationError(Exception):
    def __init__(self, reason: ReasonCode, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason: ReasonCode = reason
        self.detail = detail


def scan_banned(text: str) -> str | None:
    for pat in BANNED_PATTERNS:
        match = pat.search(text)
        if match:
            return match.group(0)
    return None


def count_sentences(text: str) -> int:
    parts = re.split(r"[.!?]+\s*", text.strip())
    return sum(1 for p in parts if p.strip())


def validate_stock_brief(payload: dict[str, object], schema: type[BaseModel]) -> BaseModel:
    """Parse StockBrief + run invariants. Raises ValidationError on violation."""
    try:
        parsed = schema.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError("schema", str(exc)) from exc

    if getattr(parsed, "not_financial_advice", None) is not True:
        raise ValidationError("not_financial_advice", "field must be literal True")

    evidence = list(getattr(parsed, "evidence", []) or [])
    if not evidence:
        raise ValidationError("empty_evidence", "evidence list is empty")

    uncertainty = str(getattr(parsed, "uncertainty", "")).strip()
    if not uncertainty:
        raise ValidationError("empty_uncertainty", "uncertainty field is empty")

    caveats = list(getattr(parsed, "caveats", []) or [])
    if not caveats:
        raise ValidationError("empty_caveats", "caveats list is empty")

    scan_fields = [
        str(getattr(parsed, "bullish_view", "")),
        str(getattr(parsed, "bearish_view", "")),
        str(getattr(parsed, "uncertainty", "")),
        str(getattr(parsed, "beginner_explanation", "")),
        *(str(c) for c in caveats),
    ]
    for text in scan_fields:
        hit = scan_banned(text)
        if hit:
            raise ValidationError("banned_phrase", f"matched {hit!r}")

    return parsed


def validate_chat_response(payload: dict[str, object], schema: type[BaseModel]) -> BaseModel:
    """Parse ChatResponse + run invariants. Raises ValidationError on violation."""
    try:
        parsed = schema.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError("schema", str(exc)) from exc

    if getattr(parsed, "not_financial_advice", None) is not True:
        raise ValidationError("not_financial_advice", "field must be literal True")

    caveats = list(getattr(parsed, "caveats", []) or [])
    if not caveats:
        raise ValidationError("empty_caveats", "caveats list is empty")

    answer = str(getattr(parsed, "answer", ""))
    for text in [answer, *(str(c) for c in caveats)]:
        hit = scan_banned(text)
        if hit:
            raise ValidationError("banned_phrase", f"matched {hit!r}")

    return parsed


def validate_news_summary(payload: dict[str, object], schema: type[BaseModel]) -> BaseModel:
    """Parse + run all invariants. Raises ValidationError on any violation."""
    try:
        parsed = schema.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError("schema", str(exc)) from exc

    summary_text = str(getattr(parsed, "summary", ""))
    if count_sentences(summary_text) > MAX_SENTENCES:
        raise ValidationError("summary_too_long", f"{count_sentences(summary_text)} sentences")

    if getattr(parsed, "not_financial_advice", None) is not True:
        raise ValidationError("not_financial_advice", "field must be literal True")

    caveats = list(getattr(parsed, "caveats", []) or [])
    confidence = float(getattr(parsed, "confidence", 0.0))
    if confidence < 0.7 and not caveats:
        raise ValidationError("empty_caveats", f"confidence={confidence:.2f} requires caveats")

    scan_targets = [summary_text, *(str(c) for c in caveats)]
    for target in scan_targets:
        hit = scan_banned(target)
        if hit:
            raise ValidationError("banned_phrase", f"matched {hit!r}")

    return parsed
