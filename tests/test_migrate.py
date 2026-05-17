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
        "schema_migrations",
    }
    assert expected.issubset(tables)


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
