"""Shared DuckDB connection helpers + price_history upsert + OHLCV read.

Keep DB-shape concerns in `packages/core/schemas/` so module callers don't repeat
upsert SQL.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import TypedDict

import duckdb
from dotenv import load_dotenv
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.schemas.models import PriceRow

DEFAULT_DB = "./data/private/sahamlens.duckdb"


class OHLCVRow(TypedDict):
    date: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: int | None


def resolve_db_path(override: str | None = None) -> Path:
    load_dotenv(".env.local")
    raw = override or os.environ.get("DUCKDB_PATH", DEFAULT_DB)
    path = Path(raw).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def open_connection(
    override: str | None = None,
    *,
    read_only: bool = False,
) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(resolve_db_path(override)), read_only=read_only)


def upsert_price_rows(conn: duckdb.DuckDBPyConnection, rows: Iterable[PriceRow]) -> int:
    """Idempotent upsert into price_history. Returns count written."""
    count = 0
    for row in rows:
        conn.execute(
            """
            INSERT INTO price_history
                (symbol, date, open, high, low, close, volume, source, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (symbol, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                source = EXCLUDED.source,
                fetched_at = EXCLUDED.fetched_at
            """,
            [
                row.symbol,
                row.date.isoformat(),
                row.open,
                row.high,
                row.low,
                row.close,
                row.volume,
                row.source,
                row.fetched_at.isoformat(),
            ],
        )
        count += 1
    return count


def load_ohlcv(
    conn: duckdb.DuckDBPyConnection,
    symbol: str,
    *,
    limit: int | None = None,
) -> list[OHLCVRow]:
    """Return OHLCV rows sorted by date ascending. `limit` keeps only N most recent dates."""
    canonical = normalize_ticker(symbol)
    if limit is None:
        rows = conn.execute(
            """
            SELECT date, open, high, low, close, volume
            FROM price_history
            WHERE symbol = ?
            ORDER BY date
            """,
            [canonical],
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT date, open, high, low, close, volume FROM (
                SELECT date, open, high, low, close, volume
                FROM price_history
                WHERE symbol = ?
                ORDER BY date DESC
                LIMIT ?
            )
            ORDER BY date
            """,
            [canonical, limit],
        ).fetchall()
    return [
        OHLCVRow(
            date=str(r[0]),
            open=float(r[1]) if r[1] is not None else None,
            high=float(r[2]) if r[2] is not None else None,
            low=float(r[3]) if r[3] is not None else None,
            close=float(r[4]) if r[4] is not None else None,
            volume=int(r[5]) if r[5] is not None else None,
        )
        for r in rows
    ]
