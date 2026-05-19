"""Smoke test: seed synthetic price_history → run CLI main → assert points written."""

from __future__ import annotations

import json
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb
import pytest
from packages.core.schemas.models import PriceRow
from packages.core.schemas.repository import upsert_price_rows

from scripts.calculate_indicators import main
from scripts.migrate import applied_versions, apply_migration, discover_migrations


def _seed_db(path: Path, symbol: str, n: int) -> None:
    with duckdb.connect(str(path)) as conn:
        applied_versions(conn)
        for migration in discover_migrations():
            apply_migration(conn, migration)
        rows = [
            PriceRow(
                symbol=symbol,
                date=date(2024, 1, 1) + timedelta(days=i),
                open=100.0 + i * 0.1,
                high=101.0 + i * 0.1,
                low=99.0 + i * 0.1,
                close=100.5 + i * 0.1,
                volume=1_000_000 + i * 1_000,
                source="yfinance",
                fetched_at=datetime(2024, 6, 1, tzinfo=UTC),
            )
            for i in range(n)
        ]
        upsert_price_rows(conn, rows)


def test_main_json_output_shape(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = tmp_path / "smoke.duckdb"
    _seed_db(db, "BBCA.JK", n=250)
    capsys.readouterr()

    rc = main(["--symbols", "BBCA", "--db", str(db), "--json"])
    assert rc == 0

    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["symbols_processed"] == ["BBCA"]
    assert payload["points_written"] > 0
    assert payload["by_status"]["ok"] == ["BBCA"]
    assert payload["by_status"]["failed"] == []
    assert payload["errors"] == {}


def test_main_no_symbols_returns_failed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = tmp_path / "empty.duckdb"
    _seed_db(db, "BBCA.JK", n=5)

    rc = main(["--db", str(db)])
    assert rc == 3


def test_main_empty_price_history_for_symbol(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = tmp_path / "no-prices.duckdb"
    _seed_db(db, "BBCA.JK", n=0)
    capsys.readouterr()

    rc = main(["--symbols", "TLKM", "--db", str(db), "--json"])
    assert rc == 2

    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["by_status"]["empty"] == ["TLKM"]
    assert payload["points_written"] == 0


def test_main_human_summary_writes_to_stdout(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = tmp_path / "human.duckdb"
    _seed_db(db, "BBCA.JK", n=250)

    rc = main(["--symbols", "BBCA", "--db", str(db)])
    assert rc == 0

    captured = capsys.readouterr()
    assert "points_written=" in captured.out
    assert "ok=" in captured.out


def test_main_failure_path_captures_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "fail.duckdb"
    _seed_db(db, "BBCA.JK", n=250)
    capsys.readouterr()

    def boom(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("synthetic-fault")

    monkeypatch.setattr(sys.modules["scripts.calculate_indicators"], "load_price_series", boom)
    rc = main(["--symbols", "BBCA", "--db", str(db), "--json"])
    assert rc == 3

    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["by_status"]["failed"] == ["BBCA"]
    assert "synthetic-fault" in payload["errors"]["BBCA"]
