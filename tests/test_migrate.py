"""Smoke test for migration runner. Uses a tempdir DB, not the private one."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from scripts.migrate import applied_versions, apply_migration, discover_migrations


def test_discover_finds_initial_migration() -> None:
    migrations = discover_migrations()
    names = [m.name for m in migrations]
    assert "0001_initial_schema.sql" in names


def test_apply_creates_expected_tables(tmp_path: Path) -> None:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        applied_versions(conn)
        for path in discover_migrations():
            apply_migration(conn, path)
        tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    expected = {
        "stocks",
        "price_history",
        "watchlist",
        "journal",
        "portfolio_position",
        "news",
        "ai_log",
        "indicator_cache",
        "ticker_lifecycle",
        "source_coverage",
        "fundamental_snapshots",
        "screener_rules",
        "screener_rule_conditions",
        "screener_runs",
        "screener_results",
        "screener_result_exclusions",
        "weekly_review_runs",
        "weekly_review_findings",
        "strategy_rules",
        "strategy_rule_evaluations",
        "strategy_rule_violations",
        "agent_log",
        "agent_write_action",
        "research_queue",
        "schema_migrations",
    }
    assert expected.issubset(tables)


def test_v1_s2_migration_creates_lifecycle_coverage_and_fundamental_schema(
    tmp_path: Path,
) -> None:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        applied_versions(conn)
        for path in discover_migrations():
            apply_migration(conn, path)

        lifecycle_columns = _columns(conn, "ticker_lifecycle")
        assert {
            "symbol",
            "lifecycle_status",
            "coverage_tier",
            "lifecycle_source",
            "coverage_source",
            "last_verified_at",
            "renamed_from",
            "renamed_to",
            "missing_data_reason",
            "screener_eligible",
            "alert_eligible",
            "ai_explanation_eligible",
            "eligibility_reason",
            "updated_at",
        }.issubset(lifecycle_columns)

        coverage_columns = _columns(conn, "source_coverage")
        assert {
            "symbol",
            "provider_name",
            "source_type",
            "provider_trust_tier",
            "availability_state",
            "freshness_state",
            "last_success_at",
            "last_checked_at",
            "missing_reason",
            "coverage_count",
        }.issubset(coverage_columns)

        fundamental_columns = _columns(conn, "fundamental_snapshots")
        assert {
            "symbol",
            "period",
            "statement_date",
            "source",
            "source_type",
            "fetched_at",
            "imported_at",
            "data_fields",
            "available_fields",
            "missing_fields",
            "completeness_state",
            "confidence_level",
            "confidence_score",
            "caveat",
            "reason",
        }.issubset(fundamental_columns)


def test_v1_s3_migration_creates_screener_schema(tmp_path: Path) -> None:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        applied_versions(conn)
        for path in discover_migrations():
            apply_migration(conn, path)

        rule_columns = _columns(conn, "screener_rules")
        assert {
            "rule_id",
            "name",
            "description",
            "required_fields",
            "required_source_types",
            "min_coverage_tier",
            "allowed_freshness_states",
            "min_fundamental_completeness",
            "min_confidence_level",
            "is_active",
            "created_at",
            "updated_at",
        }.issubset(rule_columns)

        condition_columns = _columns(conn, "screener_rule_conditions")
        assert {
            "condition_id",
            "rule_id",
            "field_name",
            "operator",
            "value_json",
            "required_source_type",
            "missing_behavior",
            "description",
        }.issubset(condition_columns)

        run_columns = _columns(conn, "screener_runs")
        assert {
            "run_id",
            "rule_id",
            "started_at",
            "completed_at",
            "status",
            "universe_count",
            "included_count",
            "excluded_count",
            "data_quality_snapshot",
            "notes",
        }.issubset(run_columns)

        result_columns = _columns(conn, "screener_results")
        assert {
            "run_id",
            "symbol",
            "result_status",
            "coverage_tier",
            "lifecycle_status",
            "freshness_state",
            "completeness_state",
            "confidence_level",
            "matched_conditions",
            "failed_conditions",
            "missing_fields",
            "exclusion_reasons",
            "caveats",
            "explanation",
            "evaluated_at",
        }.issubset(result_columns)

        exclusion_columns = _columns(conn, "screener_result_exclusions")
        assert {
            "run_id",
            "symbol",
            "reason_code",
            "reason_detail",
            "source_field",
        }.issubset(exclusion_columns)


def test_v1_s4_migration_creates_weekly_review_and_strategy_schema(tmp_path: Path) -> None:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        applied_versions(conn)
        for path in discover_migrations():
            apply_migration(conn, path)

        review_run_columns = _columns(conn, "weekly_review_runs")
        assert {
            "review_id",
            "period_start",
            "period_end",
            "generated_at",
            "status",
            "journal_entry_count",
            "reviewed_plan_count",
            "rule_evaluation_count",
            "violation_count",
            "needs_data_count",
            "summary",
            "evidence",
            "caveats",
            "created_at",
        }.issubset(review_run_columns)

        finding_columns = _columns(conn, "weekly_review_findings")
        assert {
            "finding_id",
            "review_id",
            "finding_type",
            "title",
            "detail",
            "severity",
            "evidence",
            "caveats",
            "created_at",
        }.issubset(finding_columns)

        rule_columns = _columns(conn, "strategy_rules")
        assert {
            "rule_id",
            "name",
            "description",
            "rule_category",
            "required_fields",
            "violation_code",
            "needs_data_behavior",
            "is_active",
            "created_at",
            "updated_at",
        }.issubset(rule_columns)

        evaluation_columns = _columns(conn, "strategy_rule_evaluations")
        assert {
            "evaluation_id",
            "review_id",
            "rule_id",
            "journal_id",
            "symbol",
            "evaluation_status",
            "evaluated_at",
            "evidence",
            "caveats",
            "reason",
        }.issubset(evaluation_columns)

        violation_columns = _columns(conn, "strategy_rule_violations")
        assert {
            "violation_id",
            "evaluation_id",
            "review_id",
            "rule_id",
            "journal_id",
            "symbol",
            "violation_code",
            "violation_detail",
            "evidence",
            "caveats",
            "created_at",
        }.issubset(violation_columns)


def test_v2_migration_creates_agent_runtime_schema(tmp_path: Path) -> None:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        applied_versions(conn)
        for path in discover_migrations():
            apply_migration(conn, path)

        agent_log_columns = _columns(conn, "agent_log")
        assert {
            "id",
            "session_id",
            "surface",
            "intent",
            "command_text_redacted",
            "ai_log_id",
            "context_scope",
            "redaction_applied",
            "created_at",
        }.issubset(agent_log_columns)

        write_action_columns = _columns(conn, "agent_write_action")
        assert {
            "id",
            "agent_log_id",
            "action",
            "target_ref",
            "idempotency_key",
            "status",
            "confirmed_at",
            "created_at",
        }.issubset(write_action_columns)

        research_queue_columns = _columns(conn, "research_queue")
        assert {
            "id",
            "ticker",
            "note",
            "source_surface",
            "status",
            "created_at",
            "updated_at",
        }.issubset(research_queue_columns)


def test_v2_agent_runtime_constraints_and_relations(tmp_path: Path) -> None:
    """Audit rows insert through the intended FK + idempotency path; bad data is rejected."""
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        applied_versions(conn)
        for path in discover_migrations():
            apply_migration(conn, path)

        conn.execute(
            "INSERT INTO ai_log (id, prompt_template_id, model, input_context, output, "
            "confidence, caveats_count, created_at) VALUES "
            "(1, 'stock_chat', 'claude', '{}', '{}', NULL, 0, '2026-06-15T00:00:00+00:00')"
        )
        conn.execute(
            "INSERT INTO agent_log (id, session_id, surface, intent, command_text_redacted, "
            "ai_log_id, context_scope, redaction_applied, created_at) VALUES "
            "('agent-log-1', 'sess-1', 'telegram', 'ticker_snapshot', '/ticker [redacted]', "
            "1, 'aggregate', 1, '2026-06-15T00:00:01+00:00')"
        )
        conn.execute(
            "INSERT INTO agent_write_action (id, agent_log_id, action, target_ref, "
            "idempotency_key, status, confirmed_at, created_at) VALUES "
            "('wa-1', 'agent-log-1', 'acknowledge_alert', 'event-1', 'idem-1', "
            "'pending_confirmation', NULL, '2026-06-15T00:00:02+00:00')"
        )

        # Duplicate idempotency_key must be rejected.
        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                "INSERT INTO agent_write_action (id, agent_log_id, action, target_ref, "
                "idempotency_key, status, confirmed_at, created_at) VALUES "
                "('wa-2', 'agent-log-1', 'acknowledge_alert', 'event-1', 'idem-1', "
                "'pending_confirmation', NULL, '2026-06-15T00:00:03+00:00')"
            )

        # Unknown surface must fail the CHECK constraint.
        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                "INSERT INTO agent_log (id, session_id, surface, intent, "
                "command_text_redacted, ai_log_id, context_scope, redaction_applied, "
                "created_at) VALUES ('agent-log-2', 'sess-1', 'sms', 'ticker_snapshot', "
                "'', NULL, 'none', 1, '2026-06-15T00:00:04+00:00')"
            )

        row = conn.execute(
            "SELECT a.surface, w.action FROM agent_write_action w "
            "JOIN agent_log a ON a.id = w.agent_log_id WHERE w.id = 'wa-1'"
        ).fetchone()
        assert row == ("telegram", "acknowledge_alert")


def test_idempotent_apply(tmp_path: Path) -> None:
    db = tmp_path / "test.duckdb"
    migrations = discover_migrations()
    with duckdb.connect(str(db)) as conn:
        applied_versions(conn)
        for path in migrations:
            apply_migration(conn, path)
        first = applied_versions(conn)
        already = applied_versions(conn)
        assert first == already
        assert len(first) == len(migrations)


def _columns(conn: duckdb.DuckDBPyConnection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
    return {str(row[1]) for row in rows}
