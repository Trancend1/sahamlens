"""Repo tests: indicator_cache upsert + price_history read + latest_for query."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime

import duckdb
import pytest
from packages.core.indicators.repo import (
    latest_for,
    load_price_series,
    upsert_indicator_points,
)
from packages.core.schemas.models import IndicatorPoint, PriceRow
from packages.core.schemas.repository import upsert_price_rows
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


def _point(symbol: str, d: date, indicator: str, value: float) -> IndicatorPoint:
    return IndicatorPoint(symbol=symbol, date=d, indicator=indicator, value=value)


def test_upsert_inserts_rows(conn: duckdb.DuckDBPyConnection) -> None:
    points = [
        _point("BBCA", date(2024, 1, 1), "ma_5", 100.0),
        _point("BBCA", date(2024, 1, 2), "ma_5", 101.0),
    ]
    written = upsert_indicator_points(conn, points)
    assert written == 2
    rows = conn.execute(
        "SELECT symbol, date, indicator, value FROM indicator_cache ORDER BY date"
    ).fetchall()
    assert rows == [
        ("BBCA.JK", "2024-01-01", "ma_5", 100.0),
        ("BBCA.JK", "2024-01-02", "ma_5", 101.0),
    ]


def test_upsert_idempotent_overwrite(conn: duckdb.DuckDBPyConnection) -> None:
    p1 = _point("BBCA", date(2024, 1, 1), "ma_5", 100.0)
    upsert_indicator_points(conn, [p1])
    p2 = _point("BBCA", date(2024, 1, 1), "ma_5", 999.0)
    upsert_indicator_points(conn, [p2])

    count = conn.execute("SELECT COUNT(*) FROM indicator_cache").fetchone()
    assert count is not None and count[0] == 1
    value = conn.execute("SELECT value FROM indicator_cache").fetchone()
    assert value is not None and value[0] == 999.0


def test_upsert_empty_iterable_returns_zero(conn: duckdb.DuckDBPyConnection) -> None:
    assert upsert_indicator_points(conn, []) == 0


def test_load_price_series_returns_frame(conn: duckdb.DuckDBPyConnection) -> None:
    rows = [
        PriceRow(
            symbol="BBCA",
            date=date(2024, 1, 1),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            volume=1_000_000,
            source="yfinance",
            fetched_at=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        PriceRow(
            symbol="BBCA",
            date=date(2024, 1, 2),
            open=100.5,
            high=102.0,
            low=100.0,
            close=101.5,
            volume=1_200_000,
            source="yfinance",
            fetched_at=datetime(2024, 1, 3, tzinfo=UTC),
        ),
    ]
    upsert_price_rows(conn, rows)

    df = load_price_series(conn, "BBCA")
    assert list(df.columns) == ["close", "volume"]
    assert len(df) == 2
    assert df.iloc[0]["close"] == 100.5
    assert df.iloc[1]["volume"] == 1_200_000


def test_load_price_series_skips_null_close(conn: duckdb.DuckDBPyConnection) -> None:
    rows = [
        PriceRow(
            symbol="BBCA",
            date=date(2024, 1, 1),
            open=None,
            high=None,
            low=None,
            close=None,
            volume=None,
            source="yfinance",
            fetched_at=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        PriceRow(
            symbol="BBCA",
            date=date(2024, 1, 2),
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
            volume=1_000_000,
            source="yfinance",
            fetched_at=datetime(2024, 1, 3, tzinfo=UTC),
        ),
    ]
    upsert_price_rows(conn, rows)
    df = load_price_series(conn, "bbca")
    assert len(df) == 1
    assert df.iloc[0]["close"] == 101.0


def test_load_price_series_returns_sorted(conn: duckdb.DuckDBPyConnection) -> None:
    rows = [
        PriceRow(
            symbol="BBCA",
            date=date(2024, 1, 3),
            open=None,
            high=None,
            low=None,
            close=103.0,
            volume=1_000,
            source="yfinance",
            fetched_at=datetime(2024, 1, 4, tzinfo=UTC),
        ),
        PriceRow(
            symbol="BBCA",
            date=date(2024, 1, 1),
            open=None,
            high=None,
            low=None,
            close=101.0,
            volume=1_000,
            source="yfinance",
            fetched_at=datetime(2024, 1, 4, tzinfo=UTC),
        ),
    ]
    upsert_price_rows(conn, rows)
    df = load_price_series(conn, "BBCA")
    assert df.index.is_monotonic_increasing


def test_latest_for_returns_most_recent_per_indicator(conn: duckdb.DuckDBPyConnection) -> None:
    points = [
        _point("BBCA", date(2024, 1, 1), "ma_5", 100.0),
        _point("BBCA", date(2024, 1, 2), "ma_5", 101.0),
        _point("BBCA", date(2024, 1, 2), "rsi_14", 55.0),
        _point("BBCA", date(2024, 1, 1), "rsi_14", 50.0),
    ]
    upsert_indicator_points(conn, points)
    latest = latest_for(conn, "BBCA")
    assert latest == {"ma_5": 101.0, "rsi_14": 55.0}


def test_latest_for_empty_symbol(conn: duckdb.DuckDBPyConnection) -> None:
    assert latest_for(conn, "BBCA") == {}
