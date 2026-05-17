"""Watchlist CRUD against DuckDB `watchlist` table."""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.schemas.models import WatchlistEntry


class WatchlistAlreadyExists(ValueError):
    pass


class WatchlistNotFound(KeyError):
    pass


def add_entry(
    conn: duckdb.DuckDBPyConnection,
    symbol: str,
    *,
    tag: str | None = None,
    note: str | None = None,
    added_at: datetime | None = None,
) -> WatchlistEntry:
    canonical = normalize_ticker(symbol)
    if get_entry(conn, canonical) is not None:
        raise WatchlistAlreadyExists(canonical)
    when = (added_at or datetime.now(UTC)).isoformat()
    conn.execute(
        "INSERT INTO watchlist (symbol, tag, note, added_at) VALUES (?, ?, ?, ?)",
        [canonical, tag, note, when],
    )
    entry = get_entry(conn, canonical)
    assert entry is not None
    return entry


def remove_entry(conn: duckdb.DuckDBPyConnection, symbol: str) -> None:
    canonical = normalize_ticker(symbol)
    if get_entry(conn, canonical) is None:
        raise WatchlistNotFound(canonical)
    conn.execute("DELETE FROM watchlist WHERE symbol = ?", [canonical])


def get_entry(conn: duckdb.DuckDBPyConnection, symbol: str) -> WatchlistEntry | None:
    canonical = normalize_ticker(symbol)
    row = conn.execute(
        "SELECT symbol, tag, note, added_at FROM watchlist WHERE symbol = ?",
        [canonical],
    ).fetchone()
    return _row_to_entry(row) if row else None


def list_entries(conn: duckdb.DuckDBPyConnection) -> list[WatchlistEntry]:
    rows = conn.execute(
        "SELECT symbol, tag, note, added_at FROM watchlist ORDER BY added_at, symbol"
    ).fetchall()
    return [_row_to_entry(r) for r in rows]


def _row_to_entry(row: tuple) -> WatchlistEntry:  # type: ignore[type-arg]
    symbol, tag, note, added_at = row
    return WatchlistEntry(
        symbol=symbol,
        tag=tag,
        note=note,
        added_at=datetime.fromisoformat(added_at),
    )
