from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest
from packages.core.runtime import BootstrapStep

from scripts import runtime
from scripts.migrate import apply_migration, discover_migrations

STATUS_REQUIRED_FIELDS = {
    "ok",
    "status",
    "db_path",
    "python_executable",
    "applied_migrations",
    "pending_migrations",
    "missing_tables",
    "warnings",
    "errors",
    "recommended_commands",
}

BOOTSTRAP_REQUIRED_FIELDS = {
    "ok",
    "steps",
    "status",
    "warnings",
    "errors",
    "recommended_commands",
}


def test_runtime_status_json_detects_pending_migration(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "stale.duckdb"
    with duckdb.connect(str(db_path)) as conn:
        for migration in discover_migrations()[:5]:
            apply_migration(conn, migration)
    capsys.readouterr()

    exit_code = runtime.main(["--db", str(db_path), "status", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert STATUS_REQUIRED_FIELDS.issubset(payload.keys())
    assert payload["ok"] is False
    assert payload["status"] == "stale"
    assert payload["schema_status"] == "stale"
    assert "0006" in payload["pending_migrations"]
    assert "weekly_review_runs" in payload["missing_tables"]
    assert "errors" in payload


def test_runtime_bootstrap_json_runs_migration(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "bootstrap.duckdb"

    exit_code = runtime.main(["--db", str(db_path), "bootstrap", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert BOOTSTRAP_REQUIRED_FIELDS.issubset(payload.keys())
    assert STATUS_REQUIRED_FIELDS.issubset(payload["status"].keys())
    assert payload["ok"] is True
    assert payload["status"]["schema_status"] == "ready"
    assert payload["status"]["pending_migrations"] == []
    assert payload["errors"] == []
    assert "recommended_commands" in payload


def test_runtime_status_json_is_parseable_for_missing_db(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = runtime.main(["--db", str(tmp_path / "missing.duckdb"), "status", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert STATUS_REQUIRED_FIELDS.issubset(payload.keys())
    assert payload["ok"] is False
    assert payload["status"] == "missing"
    assert payload["errors"][0]["code"] == "db_missing"


def test_runtime_bootstrap_json_is_idempotent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "idempotent.duckdb"

    first_exit = runtime.main(["--db", str(db_path), "bootstrap", "--json"])
    first = json.loads(capsys.readouterr().out)
    second_exit = runtime.main(["--db", str(db_path), "bootstrap", "--json"])
    second = json.loads(capsys.readouterr().out)

    assert first_exit == 0
    assert second_exit == 0
    assert first["ok"] is True
    assert second["ok"] is True
    assert any(
        step["name"] == "migrate" and step["status"] == "skipped" for step in second["steps"]
    )


def test_runtime_bootstrap_optional_provider_failure_is_warning(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "provider-warning.duckdb"
    runtime.main(["--db", str(db_path), "bootstrap", "--json"])
    capsys.readouterr()
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO watchlist (symbol, tag, note, added_at) VALUES (?, ?, ?, ?)",
            ["BBCA.JK", "core", None, "2026-06-03T00:00:00+00:00"],
        )

    def provider_warning(
        conn: duckdb.DuckDBPyConnection,
        symbols: list[str],
    ) -> list[BootstrapStep]:
        return [
            BootstrapStep(
                name="provider_health",
                status="warning",
                message=f"stub provider failed for {len(symbols)} symbol(s).",
                recommended_command=(
                    "uv run python -m scripts.provider_health --json refresh-yfinance --from-watchlist"
                ),
            )
        ]

    monkeypatch.setattr(runtime, "_refresh_provider_health", provider_warning)
    monkeypatch.setattr(
        runtime,
        "_refresh_coverage",
        lambda conn, symbols: [
            BootstrapStep(
                name="coverage_fundamentals",
                status="completed",
                message="stub coverage completed.",
            )
        ],
    )
    monkeypatch.setattr(
        runtime,
        "_run_screener",
        lambda conn, symbols: [
            BootstrapStep(
                name="screener",
                status="completed",
                message="stub screener completed.",
            )
        ],
    )

    exit_code = runtime.main(["--db", str(db_path), "bootstrap", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert any(
        step["name"] == "provider_health" and step["status"] == "warning"
        for step in payload["steps"]
    )
    assert payload["errors"] == []


def test_runtime_bootstrap_core_open_failure_is_structured_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = runtime.main(["--db", str(tmp_path), "bootstrap", "--json"])

    assert exit_code != 0
    payload = json.loads(capsys.readouterr().out)
    assert BOOTSTRAP_REQUIRED_FIELDS.issubset(payload.keys())
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "db_open_failed"
    assert "Traceback" not in payload["errors"][0]["message"]
