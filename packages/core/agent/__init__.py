"""Agentic research layer: pure tool contracts and safe context boundaries.

This package is network-free and import-clean: it holds the redaction/aggregation
boundaries the Hermes runtime (`services/hermes`) calls, and it reuses
`packages/core/ai` for any LLM work. It must never import `services/**`,
`scripts/**`, or `apps/web/**`. See ADR-0019.
"""

from __future__ import annotations

from packages.core.agent.exposure import (
    ExposureHolding,
    ExposureSummary,
    exposure_summary,
)
from packages.core.agent.journal_digest import JournalDigest, journal_digest

__all__ = [
    "ExposureHolding",
    "ExposureSummary",
    "JournalDigest",
    "exposure_summary",
    "journal_digest",
]
