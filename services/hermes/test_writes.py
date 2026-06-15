"""Tests for write-action confirmation: request, confirm, apply, idempotency."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb
from packages.core.agent.audit import record_agent_interaction
from scripts.migrate import applied_versions, apply_migration, discover_migrations

from services.hermes.writes import (
    WRITE_ACTIONS,
    confirm_and_apply,
    request_write_action,
)


def _migrated_db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
    return conn


def _make_agent_log(conn: duckdb.DuckDBPyConnection) -> str:
    entry = record_agent_interaction(
        conn,
        session_id="sess-test",
        surface="telegram",
        intent="alert_triage",
        command_text_redacted="test",
    )
    return entry.id


def _insert_alert(
    conn: duckdb.DuckDBPyConnection, event_id: str, ticker: str, now: datetime
) -> None:
    conn.execute(
        "INSERT INTO alert_rules (id, name, description, rule_type, ticker, "
        "parameters_json, is_active, created_at, updated_at) "
        "VALUES ('rule-1', 'Test Rule', 'test', 'price_above', ?, "
        "'{}', 1, ?, ?)",
        [ticker, now.isoformat(), now.isoformat()],
    )
    conn.execute(
        "INSERT INTO alert_evaluations (id, rule_id, evaluated_at, status, "
        "reason, data_freshness_status, confidence_status, matched, details_json) "
        "VALUES ('eval-1', 'rule-1', ?, 'success', 'test', "
        "'fresh', 'high', 1, '{}')",
        [now.isoformat()],
    )
    conn.execute(
        """
        INSERT INTO alert_events (id, rule_id, evaluation_id, ticker,
            event_type, severity, title, message, status, created_at)
        VALUES (?, 'rule-1', 'eval-1', ?,
            'price_above', 'info', 'Test', 'Test msg', 'new', ?)
        """,
        [event_id, ticker, now.isoformat()],
    )


def test_write_actions_defined() -> None:
    assert "acknowledge_alert" in WRITE_ACTIONS
    assert "mark_false_positive" in WRITE_ACTIONS
    assert "save_journal_draft" in WRITE_ACTIONS
    assert "add_research_item" in WRITE_ACTIONS


def test_request_write_action_creates_pending(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    try:
        alog_id = _make_agent_log(conn)
        result = request_write_action(
            conn,
            agent_log_id=alog_id,
            action="acknowledge_alert",
            target_ref="evt-123",
        )
        assert result.status == "pending_confirmation"
        assert result.id.startswith("write-")
        assert "konfirmasi" in result.message.lower()
    finally:
        conn.close()


def test_request_unknown_action_returns_error(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    try:
        alog_id = _make_agent_log(conn)
        result = request_write_action(
            conn,
            agent_log_id=alog_id,
            action="nonexistent_action",
        )
        assert result.status == "error"
        assert "unknown" in result.message.lower()
    finally:
        conn.close()


def test_confirm_and_apply_acknowledge(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    conn = _migrated_db(tmp_path)
    try:
        _insert_alert(conn, "alert-1", "BBRI", now)
        alog_id = _make_agent_log(conn)
        req = request_write_action(
            conn,
            agent_log_id=alog_id,
            action="acknowledge_alert",
            target_ref="alert-1",
        )
        result = confirm_and_apply(conn, idempotency_key=req.idempotency_key, now=now)
        assert result.status == "applied"
        assert "berhasil" in result.message
    finally:
        conn.close()


def test_confirm_and_apply_mark_false_positive(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    conn = _migrated_db(tmp_path)
    try:
        _insert_alert(conn, "alert-2", "BBCA", now)
        alog_id = _make_agent_log(conn)
        req = request_write_action(
            conn,
            agent_log_id=alog_id,
            action="mark_false_positive",
            target_ref="alert-2",
        )
        result = confirm_and_apply(conn, idempotency_key=req.idempotency_key, now=now)
        assert result.status == "applied"
        row = conn.execute("SELECT status FROM alert_events WHERE id = 'alert-2'").fetchone()
        assert row is not None
        assert row[0] == "marked_false_positive"
    finally:
        conn.close()


def test_confirm_and_apply_save_journal_draft(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    conn = _migrated_db(tmp_path)
    try:
        alog_id = _make_agent_log(conn)
        req = request_write_action(
            conn,
            agent_log_id=alog_id,
            action="save_journal_draft",
            target_ref="Test journal entry",
        )
        result = confirm_and_apply(conn, idempotency_key=req.idempotency_key, now=now)
        assert result.status == "applied"
        row = conn.execute("SELECT symbol, thesis FROM journal WHERE symbol = 'DRAFT'").fetchone()
        assert row is not None
        assert "Test journal entry" in row[1]
    finally:
        conn.close()


def test_confirm_and_apply_add_research_item(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    conn = _migrated_db(tmp_path)
    try:
        alog_id = _make_agent_log(conn)
        req = request_write_action(
            conn,
            agent_log_id=alog_id,
            action="add_research_item",
            target_ref="BBRI::cek dividen terbaru",
        )
        result = confirm_and_apply(conn, idempotency_key=req.idempotency_key, now=now)
        assert result.status == "applied"
        row = conn.execute(
            "SELECT ticker, note FROM research_queue WHERE ticker = 'BBRI'"
        ).fetchone()
        assert row is not None
        assert "dividen" in row[1]
    finally:
        conn.close()


def test_confirm_twice_returns_already_applied(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    conn = _migrated_db(tmp_path)
    try:
        _insert_alert(conn, "alert-3", "BBRI", now)
        alog_id = _make_agent_log(conn)
        req = request_write_action(
            conn,
            agent_log_id=alog_id,
            action="acknowledge_alert",
            target_ref="alert-3",
        )
        first = confirm_and_apply(conn, idempotency_key=req.idempotency_key, now=now)
        second = confirm_and_apply(conn, idempotency_key=req.idempotency_key, now=now)
        assert first.status == "applied"
        assert second.status == "applied" or second.status == "confirmed"
        assert "sudah" in second.message or "already" in second.message
    finally:
        conn.close()


def test_confirm_nonexistent_key(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    try:
        result = confirm_and_apply(
            conn,
            idempotency_key="nonexistent-key",
        )
        assert result.status == "not_found"
    finally:
        conn.close()


def test_request_create_agent_write_action_row(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    try:
        alog_id = _make_agent_log(conn)
        request_write_action(
            conn,
            agent_log_id=alog_id,
            action="save_journal_draft",
            target_ref="test",
        )
        rows = conn.execute("SELECT action, status FROM agent_write_action").fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "save_journal_draft"
        assert rows[0][1] == "pending_confirmation"
    finally:
        conn.close()
