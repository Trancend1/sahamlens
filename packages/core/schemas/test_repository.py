"""Tests for shared schemas/repository helpers (load_ohlcv)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb
import pytest
from packages.core.schemas.models import PriceRow
from packages.core.schemas.repository import load_ohlcv, open_connection, upsert_price_rows
from scripts.migrate import applied_versions, apply_migration, discover_migrations


@pytest.fixture
def conn() -> Iterator[duckdb.DuckDBPyConnection]:
    c = duckdb.connect(":memory:")
    applied_versions(c)
    for path in discover_migrations():
        apply_migration(c, path)
    try:
        yield c
    finally:
        c.close()


def _row(d: date) -> PriceRow:
    return PriceRow(
        symbol="BBCA",
        date=d,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1_000_000,
        source="yfinance",
        fetched_at=datetime(2024, 6, 1, tzinfo=UTC),
    )


def test_load_ohlcv_returns_sorted_ascending(conn: duckdb.DuckDBPyConnection) -> None:
    upsert_price_rows(
        conn,
        [
            _row(date(2024, 1, 3)),
            _row(date(2024, 1, 1)),
            _row(date(2024, 1, 2)),
        ],
    )
    rows = load_ohlcv(conn, "BBCA")
    assert [r["date"] for r in rows] == ["2024-01-01", "2024-01-02", "2024-01-03"]


def test_load_ohlcv_includes_full_columns(conn: duckdb.DuckDBPyConnection) -> None:
    upsert_price_rows(conn, [_row(date(2024, 1, 1))])
    rows = load_ohlcv(conn, "bbca")
    assert len(rows) == 1
    r = rows[0]
    assert r["date"] == "2024-01-01"
    assert r["open"] == 100.0
    assert r["high"] == 101.0
    assert r["low"] == 99.0
    assert r["close"] == 100.5
    assert r["volume"] == 1_000_000


def test_load_ohlcv_limit_keeps_most_recent(conn: duckdb.DuckDBPyConnection) -> None:
    upsert_price_rows(conn, [_row(date(2024, 1, 1) + timedelta(days=i)) for i in range(10)])
    rows = load_ohlcv(conn, "BBCA", limit=3)
    assert [r["date"] for r in rows] == ["2024-01-08", "2024-01-09", "2024-01-10"]


def test_load_ohlcv_empty_returns_empty_list(conn: duckdb.DuckDBPyConnection) -> None:
    assert load_ohlcv(conn, "BBCA") == []


def test_load_ohlcv_handles_null_columns(conn: duckdb.DuckDBPyConnection) -> None:
    upsert_price_rows(
        conn,
        [
            PriceRow(
                symbol="BBCA",
                date=date(2024, 1, 1),
                open=None,
                high=None,
                low=None,
                close=None,
                volume=None,
                source="yfinance",
                fetched_at=datetime(2024, 6, 1, tzinfo=UTC),
            )
        ],
    )
    rows = load_ohlcv(conn, "BBCA")
    assert rows[0]["close"] is None
    assert rows[0]["volume"] is None


def test_open_connection_can_request_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, bool]] = []

    def fake_connect(path: str, *, read_only: bool = False) -> object:
        calls.append((path, read_only))
        return object()

    monkeypatch.setattr(duckdb, "connect", fake_connect)

    db_path = tmp_path / "readonly.duckdb"
    conn = open_connection(str(db_path), read_only=True)

    assert conn is not None
    assert calls == [(str(db_path.resolve()), True)]
