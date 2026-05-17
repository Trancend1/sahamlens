"""Smoke tests for ingest_prices CLI logic.

Real yfinance never called — we substitute FakeSource.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime

import duckdb
import pytest
from packages.core.schemas.models import FetchResult, PriceRow
from packages.core.schemas.repository import upsert_price_rows
from packages.core.watchlist import add_entry
from scripts import ingest_prices
from scripts.migrate import applied_versions, apply_migration, discover_migrations


class FakeSource:
    name = "fake"

    def __init__(self, results_by_symbol: dict[str, FetchResult]) -> None:
        self._results = results_by_symbol

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> FetchResult:
        return self._results[symbol]


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


def _row_count(conn: duckdb.DuckDBPyConnection) -> int:
    row = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()
    assert row is not None
    return int(row[0])


def _row(symbol: str, day: date, close: float) -> PriceRow:
    return PriceRow(
        symbol=symbol,
        date=day,
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1,
        source="fake",
        fetched_at=datetime.now(UTC),
    )


def test_ingest_writes_rows_and_returns_ok(conn: duckdb.DuckDBPyConnection) -> None:
    results = {
        "BBCA.JK": FetchResult(
            symbol="BBCA.JK",
            source="fake",
            fetched_at=datetime.now(UTC),
            status="ok",
            rows=[_row("BBCA.JK", date(2026, 5, 12), 10000.0)],
        ),
    }
    out = ingest_prices.ingest(
        conn,
        FakeSource(results),
        ["BBCA.JK"],
        start=date(2026, 5, 1),
        end=date(2026, 5, 14),
    )

    assert out[0].status == "ok"
    count = _row_count(conn)
    assert count == 1
    assert ingest_prices.exit_code(out) == ingest_prices.EXIT_OK


def test_failed_status_skips_upsert_and_returns_3(conn: duckdb.DuckDBPyConnection) -> None:
    results = {
        "BBCA.JK": FetchResult(
            symbol="BBCA.JK",
            source="fake",
            fetched_at=datetime.now(UTC),
            status="failed",
            rows=[],
            error_message="boom",
        ),
    }
    out = ingest_prices.ingest(
        conn,
        FakeSource(results),
        ["BBCA.JK"],
        start=date(2026, 5, 1),
        end=date(2026, 5, 14),
    )
    assert ingest_prices.exit_code(out) == ingest_prices.EXIT_FAILED
    count = _row_count(conn)
    assert count == 0


def test_partial_status_returns_2(conn: duckdb.DuckDBPyConnection) -> None:
    results = {
        "BBCA.JK": FetchResult(
            symbol="BBCA.JK",
            source="fake",
            fetched_at=datetime.now(UTC),
            status="partial",
            rows=[],
        ),
    }
    out = ingest_prices.ingest(
        conn,
        FakeSource(results),
        ["BBCA.JK"],
        start=date(2026, 5, 1),
        end=date(2026, 5, 14),
    )
    assert ingest_prices.exit_code(out) == ingest_prices.EXIT_PARTIAL


def test_resolve_symbols_from_watchlist(conn: duckdb.DuckDBPyConnection) -> None:
    add_entry(conn, "BBCA")
    add_entry(conn, "TLKM")
    symbols = ingest_prices.resolve_symbols(conn, explicit=[], from_watchlist=True)
    assert set(symbols) == {"BBCA.JK", "TLKM.JK"}


def test_resolve_symbols_explicit_wins(conn: duckdb.DuckDBPyConnection) -> None:
    add_entry(conn, "BBCA")
    symbols = ingest_prices.resolve_symbols(conn, explicit=["TLKM.JK"], from_watchlist=True)
    assert symbols == ["TLKM.JK"]


def test_upsert_idempotent(conn: duckdb.DuckDBPyConnection) -> None:
    row = _row("BBCA.JK", date(2026, 5, 12), 10000.0)
    upsert_price_rows(conn, [row])
    upsert_price_rows(conn, [row])  # second time updates instead of insert
    count = _row_count(conn)
    assert count == 1
