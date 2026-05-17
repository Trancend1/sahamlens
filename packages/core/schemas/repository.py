"""Shared DuckDB connection helpers + price_history upsert.

Keep DB-shape concerns in `packages/core/schemas/` so module callers don't repeat
upsert SQL.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

import duckdb
from dotenv import load_dotenv
from packages.core.schemas.models import PriceRow

DEFAULT_DB = "./data/private/sahamlens.duckdb"


def resolve_db_path(override: str | None = None) -> Path:
    load_dotenv(".env.local")
    raw = override or os.environ.get("DUCKDB_PATH", DEFAULT_DB)
    path = Path(raw).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def open_connection(override: str | None = None) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(resolve_db_path(override)))


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
