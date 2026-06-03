from __future__ import annotations

from pathlib import Path

import duckdb
from packages.core.runtime import REQUIRED_TABLES, get_runtime_status, run_runtime_bootstrap
from scripts.migrate import apply_migration, discover_migrations


def test_runtime_status_ready_when_all_migrations_are_applied(tmp_path: Path) -> None:
    db_path = tmp_path / "fresh.duckdb"

    result = run_runtime_bootstrap(str(db_path), python_executable="python-test")
    status = get_runtime_status(str(db_path), python_executable="python-test")

    assert result.ok is True
    assert status.ok is True
    assert status.status == "ready"
    assert status.schema_status == "ready"
    assert status.pending_migrations == []
    assert status.missing_tables == []
    assert status.errors == []


def test_runtime_status_detects_pending_migration_and_missing_s4_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "stale.duckdb"
    with duckdb.connect(str(db_path)) as conn:
        for migration in discover_migrations()[:5]:
            apply_migration(conn, migration)

    status = get_runtime_status(str(db_path), python_executable="python-test")

    assert status.ok is False
    assert status.python_executable == "python-test"
    assert status.status == "stale"
    assert status.schema_status == "stale"
    assert "0006" in status.pending_migrations
    assert "weekly_review_runs" in status.missing_tables
    assert "strategy_rule_evaluations" in status.missing_tables
    assert "uv run python -m scripts.migrate" in status.recommended_commands


def test_runtime_status_detects_missing_required_tables_even_if_migrations_claim_applied(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-table.duckdb"
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for migration in discover_migrations():
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                [migration.stem.split("_", 1)[0], "2026-06-03T00:00:00+00:00"],
            )

    status = get_runtime_status(str(db_path))

    assert status.ok is False
    assert status.pending_migrations == []
    assert (set(REQUIRED_TABLES) - {"schema_migrations"}).issubset(set(status.missing_tables))
    assert any(error.code == "missing_table" for error in status.errors)


def test_runtime_status_missing_db_returns_structured_status(tmp_path: Path) -> None:
    status = get_runtime_status(str(tmp_path / "not-created.duckdb"))

    assert status.ok is False
    assert status.status == "missing"
    assert status.schema_status == "missing"
    assert status.pending_migrations
    assert status.errors[0].code == "db_missing"
    assert "uv run python -m scripts.migrate" in status.recommended_commands


def test_runtime_status_invalid_db_returns_structured_error(tmp_path: Path) -> None:
    db_path = tmp_path / "invalid.duckdb"
    db_path.write_bytes(b"not a duckdb database")

    status = get_runtime_status(str(db_path))

    assert status.ok is False
    assert status.status == "unknown"
    assert status.errors
    assert status.errors[0].code in {"db_open_failed", "db_locked"}
    assert "Traceback" not in status.errors[0].message


def test_runtime_bootstrap_applies_pending_migrations_without_required_data(tmp_path: Path) -> None:
    db_path = tmp_path / "bootstrap.duckdb"
    with duckdb.connect(str(db_path)) as conn:
        for migration in discover_migrations()[:5]:
            apply_migration(conn, migration)

    result = run_runtime_bootstrap(str(db_path), python_executable="python-test")

    assert result.ok is True
    assert result.status.schema_status == "ready"
    assert result.status.pending_migrations == []
    assert result.status.missing_tables == []
    assert result.errors == []
    assert result.recommended_commands
    assert any(step.name == "migrate" and step.status == "completed" for step in result.steps)
    assert any(step.name == "provider_health" and step.status == "skipped" for step in result.steps)


def test_runtime_bootstrap_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "idempotent.duckdb"

    first = run_runtime_bootstrap(str(db_path))
    second = run_runtime_bootstrap(str(db_path))

    assert first.ok is True
    assert second.ok is True
    assert any(step.name == "migrate" and step.status == "skipped" for step in second.steps)


def test_runtime_bootstrap_directory_path_is_structured_failure(tmp_path: Path) -> None:
    result = run_runtime_bootstrap(str(tmp_path))

    assert result.ok is False
    assert result.errors
    assert result.errors[0].code == "db_open_failed"
    assert "Traceback" not in result.errors[0].message
