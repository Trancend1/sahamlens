"""Smoke tests for V1-S4 weekly review and strategy rule CLI."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest
from packages.core.journal.models import TradePlan
from packages.core.journal.repo import create_plan

from scripts.journal_review import main
from scripts.migrate import applied_versions, apply_migration, discover_migrations


def _init_db(path: Path) -> None:
    with duckdb.connect(str(path)) as conn:
        applied_versions(conn)
        for migration in discover_migrations():
            apply_migration(conn, migration)
        create_plan(conn, _plan(1))
        create_plan(conn, _plan(2, stop_level=0.0, invalidation="", emotion=None))


def test_review_generate_and_list_outputs_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "j.duckdb"
    _init_db(db)
    capsys.readouterr()

    rc = main(
        [
            "--db",
            str(db),
            "--json",
            "review",
            "generate",
            "--start",
            "2026-05-25",
            "--end",
            "2026-06-01",
            "--review-id",
            "review-1",
        ]
    )
    assert rc == 0
    review = json.loads(capsys.readouterr().out.strip())
    assert review["review_id"] == "review-1"
    assert review["journal_entry_count"] == 2
    assert review["violation_count"] >= 3
    assert review["findings"]

    rc = main(["--db", str(db), "--json", "review", "list"])
    assert rc == 0
    reviews = json.loads(capsys.readouterr().out.strip())
    assert reviews[0]["review_id"] == "review-1"


def test_rules_evaluate_and_results_outputs_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "j.duckdb"
    _init_db(db)
    capsys.readouterr()

    rc = main(
        [
            "--db",
            str(db),
            "--json",
            "rules",
            "evaluate",
            "--start",
            "2026-05-25",
            "--end",
            "2026-06-01",
            "--review-id",
            "review-rules",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["evaluation_count"] == 12
    assert payload["violation_count"] >= 3
    assert all("buy" not in item["reason"].lower() for item in payload["evaluations"])

    rc = main(["--db", str(db), "--json", "rules", "results", "--review-id", "review-rules"])
    assert rc == 0
    results = json.loads(capsys.readouterr().out.strip())
    assert len(results) == 12
    assert any(result["evaluation_status"] == "fail" for result in results)


def test_rules_list_outputs_named_no_dsl_rules(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "j.duckdb"
    _init_db(db)
    capsys.readouterr()

    rc = main(["--db", str(db), "--json", "rules", "list"])
    assert rc == 0
    rules = json.loads(capsys.readouterr().out.strip())
    assert {rule["rule_id"] for rule in rules} >= {
        "planned_entry_present",
        "stop_loss_present",
        "thesis_present",
        "invalidation_present",
        "emotion_logged",
    }
    assert all("DSL" not in rule["description"] for rule in rules)


def _plan(plan_id: int, **overrides: object) -> TradePlan:
    data: dict[str, object] = {
        "id": plan_id,
        "symbol": "BBCA",
        "setup_type": "breakout",
        "thesis": "Breakout with visible volume support.",
        "entry_plan": "Review entry only after close above resistance.",
        "stop_level": 9100.0,
        "invalidation": "Close below prior support.",
        "target": "Prior swing high.",
        "position_size_rupiah": 10_000_000,
        "max_loss_rupiah": 250_000,
        "emotion": "calm",
        "status": "planned",
        "created_at": datetime(2026, 5, 30, tzinfo=UTC),
    }
    data.update(overrides)
    return TradePlan.model_validate(data)
