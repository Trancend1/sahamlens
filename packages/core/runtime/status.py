"""Local runtime readiness contract.

This module is intentionally framework-free. It checks the local DuckDB runtime
before UI surfaces call feature-specific tables.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import duckdb
from dotenv import load_dotenv
from pydantic import BaseModel, Field

DEFAULT_DB = "./data/private/sahamlens.duckdb"
MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "schemas" / "migrations"

SchemaStatus = Literal["ready", "stale", "missing", "unknown"]
BootstrapStepStatus = Literal["completed", "skipped", "warning", "failed"]

REQUIRED_TABLES: tuple[str, ...] = (
    "stocks",
    "price_history",
    "watchlist",
    "journal",
    "portfolio_position",
    "news",
    "ai_log",
    "indicator_cache",
    "schema_migrations",
    "provider_health",
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
)


class RuntimeWarning(BaseModel):
    code: str
    message: str
    recommended_command: str | None = None


class RuntimeErrorDetail(BaseModel):
    code: str
    message: str
    recommended_command: str | None = None


class RuntimeStatus(BaseModel):
    ok: bool
    status: SchemaStatus
    db_path: str
    python_executable: str
    applied_migrations: list[str] = Field(default_factory=list)
    pending_migrations: list[str] = Field(default_factory=list)
    missing_tables: list[str] = Field(default_factory=list)
    schema_status: SchemaStatus
    warnings: list[RuntimeWarning] = Field(default_factory=list)
    errors: list[RuntimeErrorDetail] = Field(default_factory=list)
    recommended_commands: list[str] = Field(default_factory=list)


class BootstrapStep(BaseModel):
    name: str
    status: BootstrapStepStatus
    message: str
    recommended_command: str | None = None


class BootstrapResult(BaseModel):
    ok: bool
    steps: list[BootstrapStep]
    status: RuntimeStatus
    warnings: list[RuntimeWarning] = Field(default_factory=list)
    errors: list[RuntimeErrorDetail] = Field(default_factory=list)
    recommended_commands: list[str] = Field(default_factory=list)


def resolve_db_path(override: str | None = None) -> Path:
    load_dotenv(".env.local")
    raw = override or os.environ.get("DUCKDB_PATH", DEFAULT_DB)
    return Path(raw).resolve()


def get_runtime_status(
    db_path: str | None = None,
    *,
    python_executable: str | None = None,
) -> RuntimeStatus:
    resolved = resolve_db_path(db_path)
    migrations = _discover_migrations()
    migration_versions = [_migration_version(path) for path in migrations]
    warnings: list[RuntimeWarning] = []
    recommended_commands: list[str] = []

    if not resolved.exists():
        error = RuntimeErrorDetail(
            code="db_missing",
            message="Local DuckDB file does not exist yet.",
            recommended_command="uv run python -m scripts.migrate",
        )
        return RuntimeStatus(
            ok=False,
            status="missing",
            db_path=str(resolved),
            python_executable=python_executable or sys.executable,
            applied_migrations=[],
            pending_migrations=migration_versions,
            missing_tables=list(REQUIRED_TABLES),
            schema_status="missing",
            warnings=[
                RuntimeWarning(
                    code=error.code,
                    message=error.message,
                    recommended_command=error.recommended_command,
                )
            ],
            errors=[error],
            recommended_commands=["uv run python -m scripts.migrate"],
        )

    try:
        with duckdb.connect(str(resolved)) as conn:
            tables = _list_tables(conn)
            applied = _applied_versions(conn, tables)
            pending = [version for version in migration_versions if version not in applied]
            missing_tables = [table for table in REQUIRED_TABLES if table not in tables]
            data_warnings = _data_warnings(conn, tables)
    except duckdb.Error as exc:
        error = _db_open_error(exc)
        warning = RuntimeWarning(
            code=error.code,
            message=error.message,
            recommended_command=error.recommended_command,
        )
        return RuntimeStatus(
            ok=False,
            status="unknown",
            db_path=str(resolved),
            python_executable=python_executable or sys.executable,
            schema_status="unknown",
            warnings=[warning],
            errors=[error],
            recommended_commands=[],
        )

    warnings.extend(data_warnings)
    if pending or missing_tables:
        warnings.append(
            RuntimeWarning(
                code="schema_stale",
                message="Local schema is not ready for the current V1 runtime.",
                recommended_command="uv run python -m scripts.migrate",
            )
        )
        recommended_commands.append("uv run python -m scripts.migrate")

    schema_status: SchemaStatus = "ready"
    errors: list[RuntimeErrorDetail] = []
    if pending or missing_tables:
        schema_status = "stale"
    if missing_tables:
        errors.append(
            RuntimeErrorDetail(
                code="missing_table",
                message=f"Missing required runtime table(s): {', '.join(missing_tables[:6])}.",
                recommended_command="uv run python -m scripts.migrate",
            )
        )

    return RuntimeStatus(
        ok=schema_status == "ready",
        status=schema_status,
        db_path=str(resolved),
        python_executable=python_executable or sys.executable,
        applied_migrations=applied,
        pending_migrations=pending,
        missing_tables=missing_tables,
        schema_status=schema_status,
        warnings=warnings,
        errors=errors,
        recommended_commands=recommended_commands,
    )


def run_runtime_bootstrap(
    db_path: str | None = None,
    *,
    python_executable: str | None = None,
) -> BootstrapResult:
    resolved = resolve_db_path(db_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    steps: list[BootstrapStep] = []

    try:
        conn_context = duckdb.connect(str(resolved))
    except duckdb.Error as exc:
        error = _db_open_error(exc, fallback_code="db_open_failed")
        status = RuntimeStatus(
            ok=False,
            status="unknown",
            db_path=str(resolved),
            python_executable=python_executable or sys.executable,
            schema_status="unknown",
            warnings=[
                RuntimeWarning(
                    code=error.code,
                    message=error.message,
                    recommended_command=error.recommended_command,
                )
            ],
            errors=[error],
            recommended_commands=[],
        )
        return BootstrapResult(
            ok=False,
            steps=[
                BootstrapStep(
                    name="open_db",
                    status="failed",
                    message=error.message,
                    recommended_command=error.recommended_command,
                )
            ],
            status=status,
            warnings=status.warnings,
            errors=[error],
            recommended_commands=[],
        )

    with conn_context as conn:
        applied = _ensure_schema_migrations(conn)
        pending = [
            path for path in _discover_migrations() if _migration_version(path) not in applied
        ]
        if pending:
            for migration in pending:
                _apply_migration(conn, migration)
            steps.append(
                BootstrapStep(
                    name="migrate",
                    status="completed",
                    message=f"Applied {len(pending)} pending migration(s).",
                )
            )
        else:
            steps.append(
                BootstrapStep(
                    name="migrate",
                    status="skipped",
                    message="No pending migrations.",
                )
            )

        tables = _list_tables(conn)
        if _table_count(conn, tables, "watchlist") == 0:
            steps.append(
                BootstrapStep(
                    name="provider_health",
                    status="skipped",
                    message="Watchlist is empty; provider health refresh needs symbols.",
                    recommended_command=(
                        "uv run python -m scripts.provider_health --json refresh-yfinance --from-watchlist"
                    ),
                )
            )
            steps.append(
                BootstrapStep(
                    name="coverage_fundamentals",
                    status="skipped",
                    message="Watchlist is empty; coverage refresh needs symbols.",
                    recommended_command=(
                        "uv run python -m scripts.fundamentals --json refresh-coverage --from-watchlist"
                    ),
                )
            )
            steps.append(
                BootstrapStep(
                    name="screener",
                    status="skipped",
                    message="Watchlist is empty; screener run needs symbols.",
                    recommended_command=(
                        "uv run python -m scripts.screener --json run --builtin fundamentals-basic --from-watchlist"
                    ),
                )
            )
        else:
            steps.extend(_run_watchlist_bootstrap_steps(conn))

        if _table_count(conn, tables, "journal") == 0:
            steps.append(
                BootstrapStep(
                    name="weekly_review",
                    status="skipped",
                    message="Journal is empty; weekly review generation needs journal entries.",
                    recommended_command=(
                        "uv run python -m scripts.journal_review --json review generate --start 2026-05-25 --end 2026-06-01"
                    ),
                )
            )
            steps.append(
                BootstrapStep(
                    name="strategy_rules",
                    status="skipped",
                    message="Journal is empty; strategy-rule evaluation needs journal entries.",
                    recommended_command=(
                        "uv run python -m scripts.journal_review --json rules evaluate --start 2026-05-25 --end 2026-06-01"
                    ),
                )
            )
        else:
            steps.extend(_run_journal_bootstrap_steps(conn))

    status = get_runtime_status(str(resolved), python_executable=python_executable)
    warnings = [warning for warning in status.warnings]
    for step in steps:
        if step.status in {"skipped", "warning", "failed"}:
            warnings.append(
                RuntimeWarning(
                    code=f"bootstrap_{step.status}",
                    message=f"{step.name}: {step.message}",
                    recommended_command=step.recommended_command,
                )
            )
    return BootstrapResult(
        ok=status.schema_status == "ready" and not any(step.status == "failed" for step in steps),
        steps=steps,
        status=status,
        warnings=warnings,
        errors=status.errors,
        recommended_commands=_unique_commands(
            [
                *status.recommended_commands,
                *[
                    step.recommended_command
                    for step in steps
                    if step.recommended_command is not None
                ],
            ]
        ),
    )


def _db_open_error(
    exc: duckdb.Error,
    *,
    fallback_code: str = "db_open_failed",
) -> RuntimeErrorDetail:
    raw = str(exc)
    code = "db_locked" if "lock" in raw.lower() or "locked" in raw.lower() else fallback_code
    message = (
        "Local DuckDB file is locked; close other SahamLens commands and retry."
        if code == "db_locked"
        else "Local DuckDB file could not be opened."
    )
    return RuntimeErrorDetail(
        code=code,
        message=message,
        recommended_command=None,
    )


def _unique_commands(commands: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for command in commands:
        if command in seen:
            continue
        seen.add(command)
        result.append(command)
    return result


def _discover_migrations() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql"))


def _migration_version(path: Path) -> str:
    return path.stem.split("_", 1)[0]


def _list_tables(conn: duckdb.DuckDBPyConnection) -> set[str]:
    return {str(row[0]) for row in conn.execute("SHOW TABLES").fetchall()}


def _ensure_schema_migrations(conn: duckdb.DuckDBPyConnection) -> set[str]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {str(row[0]) for row in rows}


def _applied_versions(conn: duckdb.DuckDBPyConnection, tables: Iterable[str]) -> list[str]:
    if "schema_migrations" not in set(tables):
        return []
    rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    return [str(row[0]) for row in rows]


def _apply_migration(conn: duckdb.DuckDBPyConnection, path: Path) -> None:
    version = _migration_version(path)
    conn.execute(path.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
        [version, datetime.now(UTC).isoformat()],
    )


def _data_warnings(
    conn: duckdb.DuckDBPyConnection,
    tables: set[str],
) -> list[RuntimeWarning]:
    warnings: list[RuntimeWarning] = []
    checks = [
        (
            "provider_health",
            "provider_health_empty",
            "No provider health snapshot exists yet.",
            "uv run python -m scripts.provider_health --json refresh-yfinance --from-watchlist",
        ),
        (
            "fundamental_snapshots",
            "fundamentals_empty",
            "No fundamental snapshots exist yet.",
            "uv run python -m scripts.fundamentals --json ingest --symbol BBCA --period 2026Q1",
        ),
        (
            "weekly_review_runs",
            "weekly_review_empty",
            "No weekly review has been generated yet.",
            "uv run python -m scripts.journal_review --json review generate --start 2026-05-25 --end 2026-06-01",
        ),
        (
            "strategy_rule_evaluations",
            "strategy_evaluations_empty",
            "No strategy-rule evaluation results exist yet.",
            "uv run python -m scripts.journal_review --json rules evaluate --start 2026-05-25 --end 2026-06-01",
        ),
    ]
    for table, code, message, command in checks:
        if table in tables and _table_count(conn, tables, table) == 0:
            warnings.append(
                RuntimeWarning(
                    code=code,
                    message=message,
                    recommended_command=command,
                )
            )
    return warnings


def _table_count(
    conn: duckdb.DuckDBPyConnection,
    tables: set[str],
    table: str,
) -> int:
    if table not in tables:
        return 0
    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0


def _run_watchlist_bootstrap_steps(
    conn: duckdb.DuckDBPyConnection,
) -> list[BootstrapStep]:
    _ = conn
    return []


def _run_journal_bootstrap_steps(
    conn: duckdb.DuckDBPyConnection,
) -> list[BootstrapStep]:
    steps: list[BootstrapStep] = []
    try:
        from packages.core.journal.repo import list_plans
        from packages.core.journal.review_repo import upsert_weekly_review_run
        from packages.core.journal.weekly_review import generate_weekly_journal_review
        from packages.core.strategy import (
            default_strategy_rules,
            list_strategy_rules,
            upsert_strategy_rules,
        )

        plans = list_plans(conn)
        period_end = datetime.now(UTC)
        period_start = period_end.replace(hour=0, minute=0, second=0, microsecond=0)
        if plans:
            period_start = min(plan.created_at for plan in plans)
        generated_at = datetime.now(UTC)
        rules = list_strategy_rules(conn, active_only=True)
        if not rules:
            rules = default_strategy_rules(now=generated_at)
            upsert_strategy_rules(conn, rules)
        review = generate_weekly_journal_review(
            plans,
            rules,
            review_id=f"bootstrap-weekly-review-{generated_at.date().isoformat()}",
            period_start=period_start,
            period_end=period_end,
            generated_at=generated_at,
        )
        upsert_weekly_review_run(conn, review)
        steps.append(
            BootstrapStep(
                name="weekly_review",
                status="completed",
                message=f"Generated weekly review with {review.rule_evaluation_count} rule evaluation(s).",
            )
        )
        steps.append(
            BootstrapStep(
                name="strategy_rules",
                status="completed",
                message=f"Persisted {review.rule_evaluation_count} strategy-rule evaluation(s).",
            )
        )
    except Exception as exc:
        steps.append(
            BootstrapStep(
                name="weekly_review",
                status="warning",
                message=f"Weekly review generation did not complete: {exc}",
                recommended_command=(
                    "uv run python -m scripts.journal_review --json review generate --start 2026-05-25 --end 2026-06-01"
                ),
            )
        )
        steps.append(
            BootstrapStep(
                name="strategy_rules",
                status="warning",
                message=f"Strategy-rule evaluation did not complete: {exc}",
                recommended_command=(
                    "uv run python -m scripts.journal_review --json rules evaluate --start 2026-05-25 --end 2026-06-01"
                ),
            )
        )
    return steps
