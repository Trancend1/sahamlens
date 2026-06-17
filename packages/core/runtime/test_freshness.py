"""Tests for the data freshness tracker."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import pytest
from packages.core.runtime.freshness import (
    FreshnessRecord,
    FreshnessReport,
    check_freshness,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Iterator[str]:
    path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS price_history (symbol TEXT, fetched_at TEXT, close DOUBLE)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS provider_health (provider_name TEXT, updated_at TEXT, freshness_state TEXT)"
    )
    conn.execute("INSERT INTO price_history VALUES ('BBCA', '2026-06-16T10:00:00+00:00', 10000)")
    conn.execute(
        "INSERT INTO provider_health VALUES ('yfinance', '2026-06-16T09:00:00+00:00', 'fresh')"
    )
    conn.close()
    yield str(path)
    if path.exists():
        path.unlink()


def test_empty_db(tmp_path: Path) -> None:
    path = tmp_path / "empty.duckdb"
    conn = duckdb.connect(str(path))
    conn.close()
    report = check_freshness(str(path))
    assert isinstance(report, FreshnessReport)
    # All data types → unknown when tables don't exist
    for r in report.records:
        assert r.status == "unknown"


def test_fresh_data(db_path: str) -> None:
    report = check_freshness(db_path)
    for r in report.records:
        if r.data_type == "prices":
            # threshold 24h, timestamp is < 24h old → fresh
            assert r.status == "fresh", f"prices should be fresh: {r}"
        elif r.data_type == "provider_health":
            # threshold 6h, timestamp is > 6h old → stale
            assert r.status == "stale", f"provider_health should be stale: {r}"
        else:
            assert r.status == "unknown"


def test_stale_data(tmp_path: Path) -> None:
    path = tmp_path / "stale.duckdb"
    conn = duckdb.connect(str(path))
    conn.execute("CREATE TABLE price_history (symbol TEXT, fetched_at TEXT, close DOUBLE)")
    old = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    conn.execute("INSERT INTO price_history VALUES ('BBCA', ?, 10000)", [old])
    conn.close()

    report = check_freshness(str(path))
    prices = [r for r in report.records if r.data_type == "prices"]
    assert len(prices) == 1
    assert prices[0].status == "stale"


def test_freshness_record_dataclass() -> None:
    record = FreshnessRecord(
        data_type="prices",
        status="fresh",
        last_refreshed_at="2026-06-16T10:00:00+00:00",
        age_seconds=3600.0,
        threshold_seconds=86400,
    )
    assert record.data_type == "prices"
    assert record.status == "fresh"


def test_freshness_report_properties() -> None:
    report = FreshnessReport(
        records=[
            FreshnessRecord("alerts", "fresh", "2026-06-16T10:00:00", 100, 3600),
            FreshnessRecord("prices", "stale", "2026-06-10T10:00:00", 500000, 86400),
            FreshnessRecord("news", "stale", "2026-06-11T10:00:00", 300000, 21600),
        ]
    )
    assert report.has_stale is True
    assert report.stale_count == 2
    assert report.fresh_count == 1
    assert report.stale_types == ["prices", "news"]


def test_check_freshness_missing_db(tmp_path: Path) -> None:
    path = tmp_path / "nonexistent.duckdb"
    report = check_freshness(str(path))
    assert isinstance(report, FreshnessReport)
    assert len(report.records) == 0
