"""Smoke tests for the watchlist CLI."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest
from scripts import watchlist
from scripts.migrate import applied_versions, apply_migration, discover_migrations


@pytest.fixture
def db_path(tmp_path: Path) -> Iterator[Path]:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as c:
        applied_versions(c)
        for path in discover_migrations():
            apply_migration(c, path)
    yield db


def _run(argv: list[str], db: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    rc = watchlist.main(["--db", str(db), *argv])
    out = capsys.readouterr().out
    return rc, out


def test_seed_then_list(
    db_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc, _ = _run(["seed"], db_path, capsys)
    assert rc == 0

    rc, out = _run(["--json", "list"], db_path, capsys)
    assert rc == 0
    entries = json.loads(out)
    symbols = {e["symbol"] for e in entries}
    expected = {
        "BBCA.JK",
        "BBRI.JK",
        "BBNI.JK",
        "BMRI.JK",
        "TLKM.JK",
        "ASII.JK",
        "UNVR.JK",
        "ANTM.JK",
        "ICBP.JK",
        "GGRM.JK",
    }
    assert symbols == expected


def test_add_then_remove(
    db_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc, _ = _run(["add", "BBCA", "--tag", "bank-core"], db_path, capsys)
    assert rc == 0
    rc, _ = _run(["remove", "BBCA.JK"], db_path, capsys)
    assert rc == 0
    rc, out = _run(["--json", "list"], db_path, capsys)
    assert rc == 0
    assert json.loads(out) == []


def test_add_duplicate_exits_1(
    db_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(["add", "BBCA"], db_path, capsys)
    rc = watchlist.main(["--db", str(db_path), "add", "bbca"])
    assert rc == 1


def test_remove_missing_exits_1(
    db_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = watchlist.main(["--db", str(db_path), "remove", "BBCA"])
    assert rc == 1


def test_seed_idempotent(
    db_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(["seed"], db_path, capsys)
    rc, out = _run(["--json", "seed"], db_path, capsys)
    assert rc == 0
    payload = json.loads(out)
    assert payload["added"] == []
    assert len(payload["skipped"]) == 10
