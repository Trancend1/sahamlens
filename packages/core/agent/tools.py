"""Read-only agent tool contracts (ADR-0019 M3).

Each tool is a thin, typed wrapper the Hermes runtime (`services/hermes`, M4)
will call. A tool: reads via an existing pure boundary or `packages/core/ai`,
records exactly one `agent_log` audit row, and returns a typed result envelope.
Tools never write business data and never touch a chat surface directly.

LLM-backed tools (ticker brief/chat, alert explanation) land in M4, where the
provider/router/breaker are wired and the `ai_log_id` linkage can be passed via
`record_agent_interaction(..., ai_log_id=...)`.
"""

from __future__ import annotations

import duckdb
from packages.core.agent.audit import AgentSurface, record_agent_interaction
from packages.core.agent.exposure import ExposureSummary, exposure_summary
from packages.core.agent.journal_digest import JournalDigest, journal_digest
from pydantic import BaseModel


class AgentToolResult(BaseModel):
    """Audit-linked envelope shared by every agent tool result."""

    intent: str
    agent_log_id: str
    context_scope: str
    not_financial_advice: bool = True


class ExposureToolResult(AgentToolResult):
    summary: ExposureSummary


class JournalDigestToolResult(AgentToolResult):
    digest: JournalDigest


def exposure_tool(
    conn: duckdb.DuckDBPyConnection,
    *,
    session_id: str,
    surface: AgentSurface = "cli",
) -> ExposureToolResult:
    """Aggregate-only portfolio exposure, audited. No LLM call, no raw values."""
    summary = exposure_summary(conn)
    entry = record_agent_interaction(
        conn,
        session_id=session_id,
        surface=surface,
        intent="portfolio_exposure",
        context_scope="aggregate",
        redaction_applied=True,
    )
    return ExposureToolResult(
        intent=entry.intent,
        agent_log_id=entry.id,
        context_scope=entry.context_scope,
        summary=summary,
    )


def journal_digest_tool(
    conn: duckdb.DuckDBPyConnection,
    *,
    session_id: str,
    surface: AgentSurface = "cli",
    symbol: str | None = None,
) -> JournalDigestToolResult:
    """Redacted journal digest, audited. No LLM call, no free-text or rupiah."""
    digest = journal_digest(conn, symbol=symbol)
    entry = record_agent_interaction(
        conn,
        session_id=session_id,
        surface=surface,
        intent="journal_digest",
        command_text_redacted=f"symbol={symbol}" if symbol else "",
        context_scope="journal_digest",
        redaction_applied=True,
    )
    return JournalDigestToolResult(
        intent=entry.intent,
        agent_log_id=entry.id,
        context_scope=entry.context_scope,
        digest=digest,
    )
