"""Agentic research layer: pure tool contracts and safe context boundaries.

This package is network-free and import-clean: it holds the redaction/aggregation
boundaries the Hermes runtime (`services/hermes`) calls, and it reuses
`packages/core/ai` for any LLM work. It must never import `services/**`,
`scripts/**`, or `apps/web/**`. See ADR-0019.
"""

from __future__ import annotations

from packages.core.agent.audit import (
    AgentLogEntry,
    list_agent_log,
    record_agent_interaction,
)
from packages.core.agent.exposure import (
    ExposureHolding,
    ExposureSummary,
    exposure_summary,
)
from packages.core.agent.journal_digest import JournalDigest, journal_digest
from packages.core.agent.tools import (
    AgentToolResult,
    ExposureToolResult,
    JournalDigestToolResult,
    exposure_tool,
    journal_digest_tool,
)

__all__ = [
    "AgentLogEntry",
    "AgentToolResult",
    "ExposureHolding",
    "ExposureSummary",
    "ExposureToolResult",
    "JournalDigest",
    "JournalDigestToolResult",
    "exposure_summary",
    "exposure_tool",
    "journal_digest",
    "journal_digest_tool",
    "list_agent_log",
    "record_agent_interaction",
]
