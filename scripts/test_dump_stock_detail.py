"""Smoke tests for dump_stock_detail CLI."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb
import pytest
from packages.core.indicators import INDICATOR_KEYS, compute_all, upsert_indicator_points
from packages.core.indicators.repo import load_price_series
from packages.core.schemas.models import PriceRow
from packages.core.schemas.repository import upsert_price_rows

from scripts.dump_stock_detail import main
from scripts.migrate import applied_versions, apply_migration, discover_migrations


def _seed(db: Path, symbol: str, n: int) -> None:
    with duckdb.connect(str(db)) as conn:
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
        if n > 0:
            prices = load_price_series(conn, symbol)
            upsert_indicator_points(conn, compute_all(symbol, prices))


def test_main_json_shape(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "detail.duckdb"
    _seed(db, "BBCA.JK", n=250)
    capsys.readouterr()

    rc = main(["--symbol", "BBCA", "--db", str(db)])
    assert rc == 0

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["symbol"] == "BBCA.JK"
    assert len(payload["ohlcv"]) == 250
    assert payload["first_date"] == "2024-01-01"
    assert payload["last_date"] == "2024-09-06"
    assert set(payload["indicators_series"].keys()) == set(INDICATOR_KEYS)
    for key in INDICATOR_KEYS:
        assert isinstance(payload["indicators_series"][key], list)
    assert "ma_5" in payload["indicators_latest"]


def test_main_days_limit_trims_recent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "trim.duckdb"
    _seed(db, "BBCA.JK", n=250)
    capsys.readouterr()

    rc = main(["--symbol", "BBCA", "--db", str(db), "--days", "30"])
    assert rc == 0

    payload = json.loads(capsys.readouterr().out.strip())
    assert len(payload["ohlcv"]) == 30
    for series in payload["indicators_series"].values():
        for point in series:
            assert point["date"] >= payload["first_date"]


def test_main_unknown_symbol_returns_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "empty.duckdb"
    _seed(db, "BBCA.JK", n=0)
    capsys.readouterr()

    rc = main(["--symbol", "TLKM", "--db", str(db)])
    assert rc == 2

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["ohlcv"] == []
    assert payload["first_date"] is None
    assert payload["last_date"] is None
    assert payload["indicators_latest"] == {}


def test_main_invalid_symbol_returns_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "err.duckdb"
    _seed(db, "BBCA.JK", n=0)
    capsys.readouterr()

    rc = main(["--symbol", "BAD-TICKER", "--db", str(db)])
    assert rc == 3

    payload = json.loads(capsys.readouterr().out.strip())
    assert "error" in payload
