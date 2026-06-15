"""Audit persistence for agentic interactions (ADR-0019 D4).

One `agent_log` row per agent interaction, separate from `ai_log` (which stays
per LLM call). When an interaction made an LLM call, the underlying `ai_log` id
may be linked via `ai_log_id`; pure tools (no LLM) leave it NULL. Connection is
caller-managed, matching the other repos.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

import duckdb
from pydantic import BaseModel

AgentSurface = Literal["telegram", "discord", "cli"]
ContextScope = Literal[
    "none", "aggregate", "journal_digest", "ticker", "alert", "research", "mixed"
]


class AgentLogEntry(BaseModel):
    id: str
    session_id: str
    surface: AgentSurface
    intent: str
    command_text_redacted: str
    ai_log_id: int | None
    context_scope: ContextScope
    redaction_applied: bool
    created_at: datetime


def record_agent_interaction(
    conn: duckdb.DuckDBPyConnection,
    *,
    session_id: str,
    surface: AgentSurface,
    intent: str,
    command_text_redacted: str = "",
    ai_log_id: int | None = None,
    context_scope: ContextScope = "none",
    redaction_applied: bool = True,
    now: datetime | None = None,
) -> AgentLogEntry:
    """Insert one agent_log row and return it. Writes only; never reads private data."""
    entry = AgentLogEntry(
        id=f"agent-log-{uuid4().hex}",
        session_id=session_id,
        surface=surface,
        intent=intent,
        command_text_redacted=command_text_redacted,
        ai_log_id=ai_log_id,
        context_scope=context_scope,
        redaction_applied=redaction_applied,
        created_at=now or datetime.now(UTC),
    )
    conn.execute(
        """
        INSERT INTO agent_log (
            id, session_id, surface, intent, command_text_redacted,
            ai_log_id, context_scope, redaction_applied, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            entry.id,
            entry.session_id,
            entry.surface,
            entry.intent,
            entry.command_text_redacted,
            entry.ai_log_id,
            entry.context_scope,
            1 if entry.redaction_applied else 0,
            entry.created_at.isoformat(),
        ],
    )
    return entry


def list_agent_log(
    conn: duckdb.DuckDBPyConnection,
    *,
    session_id: str | None = None,
    limit: int = 100,
) -> list[AgentLogEntry]:
    """Return agent_log entries newest-first, optionally scoped to one session."""
    where = "WHERE session_id = ?" if session_id is not None else ""
    params: list[object] = [session_id] if session_id is not None else []
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT id, session_id, surface, intent, command_text_redacted,
               ai_log_id, context_scope, redaction_applied, created_at
        FROM agent_log {where}
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [_row_to_entry(r) for r in rows]


def _row_to_entry(row: tuple[Any, ...]) -> AgentLogEntry:
    return AgentLogEntry(
        id=str(row[0]),
        session_id=str(row[1]),
        surface=row[2],
        intent=str(row[3]),
        command_text_redacted=str(row[4]),
        ai_log_id=int(row[5]) if row[5] is not None else None,
        context_scope=row[6],
        redaction_applied=bool(row[7]),
        created_at=datetime.fromisoformat(str(row[8])),
    )
