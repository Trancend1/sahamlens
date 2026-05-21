"""Smoke tests for journal CLI: plan add / list / get / update."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest

from scripts.journal import main
from scripts.migrate import applied_versions, apply_migration, discover_migrations


def _init_db(path: Path) -> None:
    with duckdb.connect(str(path)) as conn:
        applied_versions(conn)
        for migration in discover_migrations():
            apply_migration(conn, migration)


def _plan_json(symbol: str = "BBCA", **overrides: object) -> str:
    data: dict[str, object] = {
        "symbol": symbol,
        "setup_type": "breakout",
        "thesis": "Harga menembus resistance 9500",
        "entry_plan": "Beli saat close di atas 9500",
        "stop_level": 9200.0,
        "invalidation": "Close di bawah 9200",
        "target": "10200",
        "position_size_rupiah": 10_000_000,
        "max_loss_rupiah": 300_000,
        "created_at": datetime(2026, 5, 21, tzinfo=UTC).isoformat(),
    }
    data.update(overrides)
    return json.dumps(data)


def test_add_plan_outputs_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "j.duckdb"
    _init_db(db)
    capsys.readouterr()  # flush migration prints

    rc = main(["--db", str(db), "plan", "add", "--json", _plan_json()])
    assert rc == 0

    out = json.loads(capsys.readouterr().out.strip())
    assert out["symbol"] == "BBCA.JK"
    assert out["status"] == "planned"
    assert "id" in out


def test_list_plans_empty(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "j.duckdb"
    _init_db(db)
    capsys.readouterr()

    rc = main(["--db", str(db), "plan", "list"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out.strip()) == []


def test_add_then_list_shows_plan(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "j.duckdb"
    _init_db(db)
    capsys.readouterr()

    main(["--db", str(db), "plan", "add", "--json", _plan_json()])
    capsys.readouterr()

    rc = main(["--db", str(db), "plan", "list"])
    assert rc == 0
    plans = json.loads(capsys.readouterr().out.strip())
    assert len(plans) == 1
    assert plans[0]["symbol"] == "BBCA.JK"


def test_get_existing_plan(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "j.duckdb"
    _init_db(db)
    capsys.readouterr()

    main(["--db", str(db), "plan", "add", "--json", _plan_json()])
    out = json.loads(capsys.readouterr().out.strip())
    plan_id = out["id"]

    rc = main(["--db", str(db), "plan", "get", "--id", str(plan_id)])
    assert rc == 0
    fetched = json.loads(capsys.readouterr().out.strip())
    assert fetched["id"] == plan_id


def test_get_nonexistent_plan_returns_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "j.duckdb"
    _init_db(db)
    capsys.readouterr()

    rc = main(["--db", str(db), "plan", "get", "--id", "99999"])
    assert rc == 2


def test_list_filter_by_symbol(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "j.duckdb"
    _init_db(db)
    capsys.readouterr()

    main(["--db", str(db), "plan", "add", "--json", _plan_json("BBCA")])
    main(["--db", str(db), "plan", "add", "--json", _plan_json("TLKM")])
    capsys.readouterr()

    rc = main(["--db", str(db), "plan", "list", "--symbol", "BBCA"])
    assert rc == 0
    plans = json.loads(capsys.readouterr().out.strip())
    assert all(p["symbol"] == "BBCA.JK" for p in plans)


def test_update_plan_status(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "j.duckdb"
    _init_db(db)
    capsys.readouterr()

    main(["--db", str(db), "plan", "add", "--json", _plan_json()])
    plan_id = json.loads(capsys.readouterr().out.strip())["id"]

    rc = main(
        [
            "--db",
            str(db),
            "plan",
            "update",
            "--id",
            str(plan_id),
            "--status",
            "closed",
            "--result-rupiah",
            "500000",
            "--lesson",
            "Stop terlalu dekat",
        ]
    )
    assert rc == 0
    updated = json.loads(capsys.readouterr().out.strip())
    assert updated["status"] == "closed"
    assert updated["result_rupiah"] == 500000
