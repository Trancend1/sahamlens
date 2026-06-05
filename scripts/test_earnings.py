from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from scripts import earnings
from scripts.migrate import applied_versions, apply_migration, discover_migrations


def test_earnings_cli_create_list_detail_and_summary_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = tmp_path / "earnings.duckdb"
    with duckdb.connect(str(db)) as conn:
        _migrate(conn)
    capsys.readouterr()

    create_exit = earnings.main(
        [
            "--db",
            str(db),
            "--json",
            "events",
            "create",
            "--ticker",
            "BBCA",
            "--period",
            "2026-Q2",
            "--event-date",
            "2026-07-31",
            "--source-type",
            "manual",
            "--source-ref",
            "owner note",
            "--notes",
            "Revenue grew compared with prior quarter. Margin pressure remains a caveat.",
        ]
    )
    created = json.loads(capsys.readouterr().out)
    event_id = created["item"]["id"]
    list_exit = earnings.main(["--db", str(db), "--json", "events", "list"])
    events = json.loads(capsys.readouterr().out)
    detail_exit = earnings.main(
        ["--db", str(db), "--json", "events", "detail", "--event-id", event_id]
    )
    detail = json.loads(capsys.readouterr().out)
    summary_exit = earnings.main(
        ["--db", str(db), "--json", "summary", "generate", "--event-id", event_id]
    )
    summary = json.loads(capsys.readouterr().out)
    summaries_exit = earnings.main(["--db", str(db), "--json", "summaries", "list"])
    summaries = json.loads(capsys.readouterr().out)

    assert create_exit == 0
    assert list_exit == 0
    assert detail_exit == 0
    assert summary_exit == 0
    assert summaries_exit == 0
    assert created["ok"] is True
    assert events["items"][0]["ticker"] == "BBCA.JK"
    assert detail["item"]["id"] == event_id
    assert summary["item"]["earnings_event_id"] == event_id
    assert summary["item"]["caveats"]
    assert summaries["items"][0]["confidence_status"] == "manual_only"
    combined = json.dumps([created, events, detail, summary, summaries]).lower()
    assert "traceback" not in combined
    assert "buy" not in combined
    assert "profit opportunity" not in combined


def test_earnings_cli_insufficient_notes_returns_structured_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = tmp_path / "earnings.duckdb"
    with duckdb.connect(str(db)) as conn:
        _migrate(conn)
    capsys.readouterr()
    earnings.main(
        [
            "--db",
            str(db),
            "--json",
            "events",
            "create",
            "--ticker",
            "BBCA",
            "--period",
            "2026-Q2",
            "--event-date",
            "2026-07-31",
            "--source-type",
            "manual",
        ]
    )
    event = json.loads(capsys.readouterr().out)

    exit_code = earnings.main(
        [
            "--db",
            str(db),
            "--json",
            "summary",
            "generate",
            "--event-id",
            event["item"]["id"],
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert payload["ok"] is False
    assert payload["status"] == "insufficient_data"
    assert payload["errors"][0]["code"] == "insufficient_data"
    assert "Traceback" not in json.dumps(payload)


def test_earnings_cli_missing_schema_returns_structured_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = tmp_path / "stale.duckdb"
    with duckdb.connect(str(db)) as conn:
        for migration in discover_migrations()[:6]:
            apply_migration(conn, migration)
    capsys.readouterr()

    exit_code = earnings.main(["--db", str(db), "--json", "events", "list"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert payload["ok"] is False
    assert payload["status"] == "schema_stale"
    assert payload["errors"][0]["code"] in {"schema_stale", "missing_table"}
    assert "uv run python -m scripts.migrate" in payload["recommended_commands"]
    assert "Traceback" not in json.dumps(payload)


def _migrate(conn: duckdb.DuckDBPyConnection) -> None:
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
