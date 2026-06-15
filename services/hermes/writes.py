"""Write-action confirmation and application (M4.5).

Flow: pending_confirmation -> confirmed -> applied.
All write actions require explicit user confirmation.
Idempotency is enforced via UNIQUE constraint on idempotency_key.
acknowledge/mark_false_positive reuse the V1-S6 alert lifecycle.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import duckdb
from packages.core.alerts.repo import (
    acknowledge_alert_event,
    mark_alert_event_false_positive,
)
from pydantic import BaseModel

WRITE_ACTIONS: frozenset[str] = frozenset(
    {
        "acknowledge_alert",
        "mark_false_positive",
        "save_journal_draft",
        "add_research_item",
    }
)


class WriteActionResult(BaseModel):
    id: str
    idempotency_key: str = ""
    action: str = ""
    status: str = ""
    message: str = ""


def request_write_action(
    conn: duckdb.DuckDBPyConnection,
    *,
    agent_log_id: str,
    action: str,
    target_ref: str | None = None,
) -> WriteActionResult:
    """Create a pending write action row. Raises on duplicate idempotency_key."""
    if action not in WRITE_ACTIONS:
        return WriteActionResult(
            id="",
            action=action,
            status="error",
            message=f"Unknown write action: {action}",
        )

    idempotency_key = f"{agent_log_id}::{action}::{target_ref or ''}"
    write_id = f"write-{uuid4().hex}"
    now = datetime.now(UTC)

    conn.execute(
        """
        INSERT INTO agent_write_action
            (id, agent_log_id, action, target_ref, idempotency_key,
             status, created_at)
        VALUES (?, ?, ?, ?, ?, 'pending_confirmation', ?)
        """,
        [write_id, agent_log_id, action, target_ref, idempotency_key, now.isoformat()],
    )
    return WriteActionResult(
        id=write_id,
        idempotency_key=idempotency_key,
        action=action,
        status="pending_confirmation",
        message=f"Konfirmasi dibutuhkan untuk {action}. Balas 'yes' untuk konfirmasi.",
    )


def confirm_and_apply(
    conn: duckdb.DuckDBPyConnection,
    *,
    idempotency_key: str,
    now: datetime | None = None,
) -> WriteActionResult:
    """Confirm a pending write action and apply it."""
    ts = now or datetime.now(UTC)

    row = conn.execute(
        """
        SELECT id, agent_log_id, action, target_ref, status
        FROM agent_write_action WHERE idempotency_key = ?
        """,
        [idempotency_key],
    ).fetchone()

    if row is None:
        return WriteActionResult(
            id="",
            idempotency_key=idempotency_key,
            action="",
            status="not_found",
            message="Write action tidak ditemukan. Mungkin sudah diapply atau expired.",
        )

    write_id, _agent_log_id, action, target_ref, current_status = row

    if current_status != "pending_confirmation":
        return WriteActionResult(
            id=write_id,
            idempotency_key=idempotency_key,
            action=action,
            status=current_status,
            message=f"Write action sudah {current_status}.",
        )

    conn.execute(
        "UPDATE agent_write_action SET status = 'confirmed', confirmed_at = ? WHERE id = ?",
        [ts.isoformat(), write_id],
    )

    try:
        _apply_action(conn, action, target_ref, ts)
    except Exception as exc:
        conn.execute(
            "UPDATE agent_write_action SET status = 'rejected' WHERE id = ?",
            [write_id],
        )
        return WriteActionResult(
            id=write_id,
            idempotency_key=idempotency_key,
            action=action,
            status="rejected",
            message=f"Gagal mengaplikasikan: {exc}",
        )

    conn.execute(
        "UPDATE agent_write_action SET status = 'applied' WHERE id = ?",
        [write_id],
    )
    return WriteActionResult(
        id=write_id,
        idempotency_key=idempotency_key,
        action=action,
        status="applied",
        message=f"{action} berhasil diapply.",
    )


def _apply_action(
    conn: duckdb.DuckDBPyConnection,
    action: str,
    target_ref: str | None,
    now: datetime,
) -> None:
    if action == "acknowledge_alert":
        if not target_ref:
            raise ValueError("alert_event_id diperlukan untuk acknowledge_alert")
        result = acknowledge_alert_event(conn, target_ref, now=now)
        if result is None:
            raise ValueError(f"Alert event {target_ref} tidak ditemukan")

    elif action == "mark_false_positive":
        if not target_ref:
            raise ValueError("alert_event_id diperlukan untuk mark_false_positive")
        result = mark_alert_event_false_positive(conn, target_ref, now=now)
        if result is None:
            raise ValueError(f"Alert event {target_ref} tidak ditemukan")

    elif action == "save_journal_draft":
        draft_text = (target_ref or "")[:500]
        conn.execute(
            """
            INSERT INTO journal
                (id, symbol, setup_type, thesis, entry_plan, stop_level,
                 invalidation, target, position_size_rupiah, max_loss_rupiah,
                 emotion, status, result_rupiah, lesson, created_at, reviewed_at)
            VALUES (?, 'DRAFT', 'other', ?, '', 0.0, '', '', 0, 0,
                    NULL, 'planned', NULL, NULL, ?, NULL)
            """,
            [int(now.timestamp() * 1_000_000), draft_text, now.isoformat()],
        )

    elif action == "add_research_item":
        parts = (target_ref or "").split("::", 1)
        ticker = parts[0] if len(parts) > 0 else ""
        note = parts[1] if len(parts) > 1 else ""
        if not ticker or not note:
            raise ValueError("research_item butuh ticker dan note (format: SYMBOL::note)")
        conn.execute(
            """
            INSERT INTO research_queue
                (id, ticker, note, source_surface, status, created_at, updated_at)
            VALUES (?, ?, ?, 'telegram', 'open', ?, ?)
            """,
            [f"rq-{uuid4().hex}", ticker, note, now.isoformat(), now.isoformat()],
        )
