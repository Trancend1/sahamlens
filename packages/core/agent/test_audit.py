"""agent_log audit repo: insert, list, FK to ai_log, redaction default."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest
from packages.core.agent.audit import (
    list_agent_log,
    record_agent_interaction,
)
from packages.core.news.repo import log_ai_call
from scripts.migrate import applied_versions, apply_migration, discover_migrations


def _migrated_db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
    return conn


def test_record_inserts_and_returns_entry(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        entry = record_agent_interaction(
            conn,
            session_id="sess-1",
            surface="telegram",
            intent="portfolio_exposure",
            context_scope="aggregate",
        )
        stored = list_agent_log(conn, session_id="sess-1")

    assert entry.id.startswith("agent-log-")
    assert entry.redaction_applied is True
    assert entry.ai_log_id is None
    assert len(stored) == 1
    assert stored[0].id == entry.id
    assert stored[0].context_scope == "aggregate"


def test_links_to_ai_log_when_provided(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        ai_log_id = log_ai_call(
            conn,
            prompt_template_id="stock_brief",
            model="claude",
            input_context="{}",
            output="{}",
            confidence=None,
            caveats_count=0,
        )
        entry = record_agent_interaction(
            conn,
            session_id="sess-1",
            surface="cli",
            intent="ticker_brief",
            ai_log_id=ai_log_id,
            context_scope="ticker",
        )
        stored = list_agent_log(conn, session_id="sess-1")[0]

    assert entry.ai_log_id == ai_log_id
    assert stored.ai_log_id == ai_log_id


def test_dangling_ai_log_fk_is_rejected(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn, pytest.raises(duckdb.ConstraintException):
        record_agent_interaction(
            conn,
            session_id="sess-1",
            surface="cli",
            intent="ticker_brief",
            ai_log_id=999_999,  # no such ai_log row
        )


def test_list_orders_newest_first_and_scopes_by_session(tmp_path: Path) -> None:
    base = datetime(2026, 6, 15, tzinfo=UTC)
    with _migrated_db(tmp_path) as conn:
        record_agent_interaction(conn, session_id="a", surface="cli", intent="one", now=base)
        record_agent_interaction(
            conn,
            session_id="a",
            surface="cli",
            intent="two",
            now=base.replace(minute=5),
        )
        record_agent_interaction(conn, session_id="b", surface="cli", intent="other", now=base)
        scoped = list_agent_log(conn, session_id="a")
        everything = list_agent_log(conn)

    assert [e.intent for e in scoped] == ["two", "one"]
    assert len(everything) == 3
