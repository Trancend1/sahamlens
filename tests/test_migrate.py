"""Smoke test for migration runner. Uses a tempdir DB, not the private one."""

from __future__ import annotations

from pathlib import Path

import duckdb
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
