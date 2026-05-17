"""CRUD tests against an in-memory DuckDB seeded with migrations."""

from __future__ import annotations

from collections.abc import Iterator

import duckdb
import pytest
from packages.core.watchlist import (
    WatchlistAlreadyExists,
    WatchlistNotFound,
    add_entry,
    get_entry,
    list_entries,
    remove_entry,
)
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


def test_add_then_get(conn: duckdb.DuckDBPyConnection) -> None:
    entry = add_entry(conn, "bbca", tag="bank-core", note="big bank")
    assert entry.symbol == "BBCA.JK"
    assert entry.tag == "bank-core"
    fetched = get_entry(conn, "BBCA.JK")
    assert fetched is not None
    assert fetched.symbol == "BBCA.JK"


def test_add_duplicate_rejected(conn: duckdb.DuckDBPyConnection) -> None:
    add_entry(conn, "BBCA.JK")
    with pytest.raises(WatchlistAlreadyExists):
        add_entry(conn, "bbca")


def test_remove_existing(conn: duckdb.DuckDBPyConnection) -> None:
    add_entry(conn, "TLKM")
    remove_entry(conn, "tlkm.jk")
    assert get_entry(conn, "TLKM.JK") is None


def test_remove_missing_raises(conn: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(WatchlistNotFound):
        remove_entry(conn, "BBCA.JK")


def test_list_sorted_by_added_at(conn: duckdb.DuckDBPyConnection) -> None:
    from datetime import UTC, datetime

    add_entry(conn, "BBRI", added_at=datetime(2026, 5, 1, tzinfo=UTC))
    add_entry(conn, "TLKM", added_at=datetime(2026, 5, 3, tzinfo=UTC))
    add_entry(conn, "BBCA", added_at=datetime(2026, 5, 2, tzinfo=UTC))

    symbols = [e.symbol for e in list_entries(conn)]
    assert symbols == ["BBRI.JK", "BBCA.JK", "TLKM.JK"]


def test_invalid_symbol_rejected(conn: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(ValueError):
        add_entry(conn, "BAD-TICKER")
