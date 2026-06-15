"""Read-only tool contracts: typed result + exactly one audit row, leak-free."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from packages.core.agent.audit import list_agent_log
from packages.core.agent.tools import exposure_tool, journal_digest_tool
from packages.core.journal.models import TradePlan
from packages.core.journal.repo import create_plan
from packages.core.portfolio.models import PortfolioPosition
from packages.core.portfolio.repo import replace_positions
from scripts.migrate import applied_versions, apply_migration, discover_migrations


def _migrated_db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
    return conn


def test_exposure_tool_returns_result_and_writes_one_audit_row(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        replace_positions(
            conn,
            [
                PortfolioPosition(
                    symbol="BBCA",
                    lots=7777,
                    avg_price=9999.99,
                    imported_at=datetime.now(UTC),
                    source="csv",
                )
            ],
        )
        result = exposure_tool(conn, session_id="sess-1", surface="telegram")
        rows = list_agent_log(conn, session_id="sess-1")

    assert result.intent == "portfolio_exposure"
    assert result.context_scope == "aggregate"
    assert result.summary.position_count == 1
    assert len(rows) == 1
    assert rows[0].id == result.agent_log_id
    assert rows[0].redaction_applied is True
    # Audit envelope + payload must not leak raw lots/avg_price.
    payload = json.dumps(result.model_dump(), ensure_ascii=False)
    assert "7777" not in payload
    assert "9999.99" not in payload


def test_journal_digest_tool_audits_scope_and_symbol(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        create_plan(
            conn,
            TradePlan(
                id=1,
                symbol="BBCA",
                setup_type="breakout",
                thesis="PRIVATETHESIS",
                entry_plan="PRIVATEENTRY",
                stop_level=9000.0,
                invalidation="below 9000",
                target="PRIVATETARGET",
                position_size_rupiah=123456789,
                max_loss_rupiah=87654321,
                emotion="calm",
                created_at=datetime.now(UTC),
            ),
        )
        result = journal_digest_tool(conn, session_id="sess-1", symbol="BBCA")
        rows = list_agent_log(conn, session_id="sess-1")

    assert result.intent == "journal_digest"
    assert result.context_scope == "journal_digest"
    assert result.digest.entry_count == 1
    assert len(rows) == 1
    assert rows[0].command_text_redacted == "symbol=BBCA"
    payload = json.dumps(result.model_dump(), ensure_ascii=False)
    for sentinel in ("PRIVATETHESIS", "PRIVATEENTRY", "PRIVATETARGET", "123456789", "87654321"):
        assert sentinel not in payload
