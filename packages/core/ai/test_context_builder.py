"""Tests for context_builder.build_stock_context."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import duckdb
import pytest
from packages.core.ai.context_builder import StockContext, build_stock_context
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


def _seed_prices(conn: duckdb.DuckDBPyConnection, symbol: str = "BBCA.JK") -> None:
    now = datetime.now(UTC).isoformat()
    rows = [
        (symbol, "2026-05-19", 9400.0, 9500.0, 9350.0, 9450.0, 10_000_000, "yfinance", now),
        (symbol, "2026-05-20", 9450.0, 9550.0, 9400.0, 9480.0, 12_000_000, "yfinance", now),
        (symbol, "2026-05-21", 9480.0, 9600.0, 9450.0, 9550.0, 11_000_000, "yfinance", now),
    ]
    conn.executemany(
        "INSERT INTO price_history (symbol, date, open, high, low, close, volume, source, fetched_at)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        rows,
    )


def test_build_returns_stock_context(conn: duckdb.DuckDBPyConnection) -> None:
    _seed_prices(conn)
    ctx = build_stock_context(conn, "BBCA")
    assert isinstance(ctx, StockContext)
    assert ctx.symbol == "BBCA.JK"


def test_price_context_populated(conn: duckdb.DuckDBPyConnection) -> None:
    _seed_prices(conn)
    ctx = build_stock_context(conn, "BBCA")
    assert ctx.price is not None
    assert ctx.price.last_close == 9550.0
    assert ctx.price.prev_close == 9480.0
    assert ctx.price.last_date == "2026-05-21"


def test_change_pct_calculated(conn: duckdb.DuckDBPyConnection) -> None:
    _seed_prices(conn)
    ctx = build_stock_context(conn, "BBCA")
    assert ctx.price is not None
    expected = ((9550.0 - 9480.0) / 9480.0) * 100
    assert abs(ctx.price.change_pct - expected) < 0.01


def test_high_low_90d_correct(conn: duckdb.DuckDBPyConnection) -> None:
    _seed_prices(conn)
    ctx = build_stock_context(conn, "BBCA")
    assert ctx.price is not None
    assert ctx.price.high_90d == 9600.0
    assert ctx.price.low_90d == 9350.0


def test_no_data_returns_none_price(conn: duckdb.DuckDBPyConnection) -> None:
    ctx = build_stock_context(conn, "TLKM")
    assert ctx.price is None
    assert ctx.indicators == {}


def test_as_text_contains_symbol(conn: duckdb.DuckDBPyConnection) -> None:
    _seed_prices(conn)
    ctx = build_stock_context(conn, "BBCA")
    text = ctx.as_text()
    assert "9550" in text or "Harga" in text


def test_as_text_no_data_graceful(conn: duckdb.DuckDBPyConnection) -> None:
    ctx = build_stock_context(conn, "TLKM")
    text = ctx.as_text()
    assert "tidak tersedia" in text.lower() or "belum" in text.lower()
