"""Tests for portfolio repo — upsert, list, delete."""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb
import pytest
from packages.core.portfolio.models import PortfolioPosition
from packages.core.portfolio.repo import (
    delete_all,
    list_positions,
    replace_positions,
    upsert_positions,
)


@pytest.fixture()
def conn() -> duckdb.DuckDBPyConnection:
    db = duckdb.connect(":memory:")
    db.execute(
        """
        CREATE TABLE portfolio_position (
            symbol TEXT,
            lots INTEGER,
            avg_price REAL,
            imported_at TEXT,
            source TEXT,
            PRIMARY KEY (symbol, imported_at)
        )
        """
    )
    return db


def _pos(symbol: str, lots: int = 5, price: float = 1000.0) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        lots=lots,
        avg_price=price,
        imported_at=datetime(2026, 5, 22, tzinfo=UTC),
        source="csv",
    )


class TestUpsertPositions:
    def test_inserts_positions(self, conn: duckdb.DuckDBPyConnection) -> None:
        count = upsert_positions(conn, [_pos("BBCA.JK"), _pos("BBRI.JK")])
        assert count == 2
        rows = conn.execute("SELECT count(*) FROM portfolio_position").fetchone()
        assert rows is not None and rows[0] == 2

    def test_empty_list_returns_zero(self, conn: duckdb.DuckDBPyConnection) -> None:
        assert upsert_positions(conn, []) == 0

    def test_idempotent_on_replace(self, conn: duckdb.DuckDBPyConnection) -> None:
        pos = _pos("BBCA.JK")
        upsert_positions(conn, [pos])
        upsert_positions(conn, [pos])  # same PK → replace
        count = conn.execute("SELECT count(*) FROM portfolio_position").fetchone()
        assert count is not None and count[0] == 1


class TestDeleteAll:
    def test_removes_all_rows(self, conn: duckdb.DuckDBPyConnection) -> None:
        upsert_positions(conn, [_pos("BBCA.JK"), _pos("BBRI.JK")])
        delete_all(conn)
        count = conn.execute("SELECT count(*) FROM portfolio_position").fetchone()
        assert count is not None and count[0] == 0

    def test_delete_on_empty_is_noop(self, conn: duckdb.DuckDBPyConnection) -> None:
        delete_all(conn)  # should not raise
        count = conn.execute("SELECT count(*) FROM portfolio_position").fetchone()
        assert count is not None and count[0] == 0


class TestReplacePositions:
    def test_atomic_replace(self, conn: duckdb.DuckDBPyConnection) -> None:
        upsert_positions(conn, [_pos("BBCA.JK"), _pos("BBRI.JK")])
        count = replace_positions(conn, [_pos("TLKM.JK")])
        assert count == 1
        rows = list_positions(conn)
        assert len(rows) == 1
        assert rows[0].symbol == "TLKM.JK"


class TestListPositions:
    def test_sorted_by_symbol(self, conn: duckdb.DuckDBPyConnection) -> None:
        upsert_positions(conn, [_pos("TLKM.JK"), _pos("BBCA.JK"), _pos("BBRI.JK")])
        rows = list_positions(conn)
        syms = [r.symbol for r in rows]
        assert syms == sorted(syms)

    def test_returns_correct_types(self, conn: duckdb.DuckDBPyConnection) -> None:
        upsert_positions(conn, [_pos("BBCA.JK", lots=10, price=9200.0)])
        rows = list_positions(conn)
        assert rows[0].lots == 10
        assert rows[0].avg_price == 9200.0
        assert rows[0].source == "csv"

    def test_empty_table_returns_empty_list(self, conn: duckdb.DuckDBPyConnection) -> None:
        assert list_positions(conn) == []
