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
