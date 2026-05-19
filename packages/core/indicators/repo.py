"""DuckDB I/O for indicator_cache + price_history read helper.

Caller passes `conn` explicitly (mirror packages/core/schemas/repository.py pattern).
"""

from __future__ import annotations

from collections.abc import Iterable

import duckdb
import pandas as pd
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.schemas.models import IndicatorPoint


def upsert_indicator_points(
    conn: duckdb.DuckDBPyConnection, points: Iterable[IndicatorPoint]
) -> int:
    """Idempotent upsert into indicator_cache. Returns count written."""
    count = 0
    for p in points:
        conn.execute(
            """
            INSERT INTO indicator_cache (symbol, date, indicator, value)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (symbol, date, indicator) DO UPDATE SET value = EXCLUDED.value
            """,
            [p.symbol, p.date.isoformat(), p.indicator, p.value],
        )
        count += 1
    return count


def load_price_series(conn: duckdb.DuckDBPyConnection, symbol: str) -> pd.DataFrame:
    """Return DataFrame indexed by date with columns `close` + `volume`. Skips null close."""
    canonical = normalize_ticker(symbol)
    rows = conn.execute(
        """
        SELECT date, close, volume
        FROM price_history
        WHERE symbol = ? AND close IS NOT NULL
        ORDER BY date
        """,
        [canonical],
    ).fetchall()
    if not rows:
        return pd.DataFrame(columns=["close", "volume"], dtype="float64")
    dates = pd.DatetimeIndex([pd.Timestamp(r[0]) for r in rows], name="date")
    return pd.DataFrame(
        {
            "close": [float(r[1]) for r in rows],
            "volume": [float(r[2]) if r[2] is not None else 0.0 for r in rows],
        },
        index=dates,
    )


def latest_for(conn: duckdb.DuckDBPyConnection, symbol: str) -> dict[str, float]:
    """Return `{indicator: value}` from the most recent row per indicator for a symbol."""
    canonical = normalize_ticker(symbol)
    rows = conn.execute(
        """
        SELECT indicator, value
        FROM indicator_cache ic
        WHERE symbol = ?
          AND date = (
              SELECT MAX(date) FROM indicator_cache
              WHERE symbol = ic.symbol AND indicator = ic.indicator
          )
        """,
        [canonical],
    ).fetchall()
    return {row[0]: float(row[1]) for row in rows}
