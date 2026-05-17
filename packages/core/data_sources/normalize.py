"""Canonical IDX ticker normalization. Mirror DATA_SOURCES.md §2."""

from __future__ import annotations

import re

TICKER_RE = re.compile(r"^[A-Z0-9]{4}\.JK$")


def normalize_ticker(raw: str) -> str:
    """Return canonical `XXXX.JK` ticker. Raise ValueError on invalid input."""
    if not isinstance(raw, str):
        raise ValueError(f"Ticker must be str, got {type(raw).__name__}")
    cleaned = raw.strip().upper()
    if not cleaned:
        raise ValueError("Empty ticker")
    if not cleaned.endswith(".JK"):
        cleaned = f"{cleaned}.JK"
    if not TICKER_RE.match(cleaned):
        raise ValueError(f"Invalid IDX ticker: {raw!r}")
    return cleaned
