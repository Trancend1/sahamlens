"""DuckDB persistence for portfolio positions.

Replace-on-import: delete_all then upsert_positions in one transaction.
Connection is caller-managed.
"""

from __future__ import annotations

from typing import Any

import duckdb
from packages.core.portfolio.models import PortfolioPosition


def upsert_positions(
    conn: duckdb.DuckDBPyConnection,
    positions: list[PortfolioPosition],
) -> int:
    """Insert positions. Caller must call delete_all first for a clean replace."""
    if not positions:
        return 0
    conn.executemany(
        """
        INSERT OR REPLACE INTO portfolio_position
            (symbol, lots, avg_price, imported_at, source)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            [
                p.symbol,
                p.lots,
                p.avg_price,
                p.imported_at.isoformat(),
                p.source,
            ]
            for p in positions
        ],
    )
    return len(positions)


def delete_all(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("DELETE FROM portfolio_position")


def replace_positions(
    conn: duckdb.DuckDBPyConnection,
    positions: list[PortfolioPosition],
) -> int:
    """Atomic replace: delete all then insert. Returns count inserted."""
    delete_all(conn)
    return upsert_positions(conn, positions)


def list_positions(conn: duckdb.DuckDBPyConnection) -> list[PortfolioPosition]:
    """Return all positions sorted by symbol, latest import_at per symbol."""
    rows: list[Any] = conn.execute(
        """
        SELECT symbol, lots, avg_price, imported_at, source
        FROM portfolio_position
        ORDER BY symbol
        """
    ).fetchall()
    return [_row_to_position(r) for r in rows]


def _row_to_position(row: tuple[Any, ...]) -> PortfolioPosition:
    symbol, lots, avg_price, imported_at, source = row
    return PortfolioPosition(
        symbol=symbol,
        lots=int(lots),
        avg_price=float(avg_price),
        imported_at=imported_at,
        source=source,
    )
