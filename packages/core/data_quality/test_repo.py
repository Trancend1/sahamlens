"""Repository tests for provider health persistence."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import duckdb
import pytest
from packages.core.data_quality.models import ProviderHealthSnapshot
from packages.core.data_quality.repo import (
    list_provider_health_snapshots,
    load_data_quality_overview,
    upsert_provider_health_snapshot,
)
from scripts.migrate import applied_versions, apply_migration, discover_migrations

NOW = datetime(2026, 5, 31, 9, 0, tzinfo=UTC)
EARLIER = datetime(2026, 5, 31, 8, 0, tzinfo=UTC)


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


def _snapshot(
    provider_name: str,
    freshness_state: str,
    *,
    coverage_count: int | None = 10,
) -> ProviderHealthSnapshot:
    kwargs: dict[str, object] = {
        "provider_name": provider_name,
        "provider_trust_tier": "tier_3",
        "source_type": "ohlcv",
        "freshness_state": freshness_state,
        "updated_at": NOW,
        "coverage_count": coverage_count,
    }
    if freshness_state in {"fresh", "delayed", "stale", "partial"}:
        kwargs["last_success_at"] = EARLIER
    if freshness_state == "failed":
        kwargs["last_failure_at"] = NOW
        kwargs["last_failure_reason"] = "429 rate limited"
        kwargs["consecutive_failure_count"] = 2
    return ProviderHealthSnapshot.model_validate(kwargs)


def test_provider_health_table_exists_after_migration(conn: duckdb.DuckDBPyConnection) -> None:
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = 'provider_health'
        """
    ).fetchone()
    assert row is not None
    assert int(row[0]) == 1


def test_upsert_and_list_provider_health_snapshot(conn: duckdb.DuckDBPyConnection) -> None:
    snapshot = _snapshot("yfinance", "failed")

    assert upsert_provider_health_snapshot(conn, snapshot) == 1

    rows = list_provider_health_snapshots(conn)
    assert rows == [snapshot]


def test_upsert_replaces_same_provider_and_source_type(conn: duckdb.DuckDBPyConnection) -> None:
    upsert_provider_health_snapshot(conn, _snapshot("yfinance", "stale", coverage_count=3))
    upsert_provider_health_snapshot(conn, _snapshot("yfinance", "fresh", coverage_count=5))

    rows = list_provider_health_snapshots(conn)
    assert len(rows) == 1
    assert rows[0].freshness_state == "fresh"
    assert rows[0].coverage_count == 5


def test_load_data_quality_overview_uses_persisted_snapshots(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    upsert_provider_health_snapshot(conn, _snapshot("yfinance", "fresh", coverage_count=3))
    upsert_provider_health_snapshot(conn, _snapshot("rss", "stale", coverage_count=2))
    upsert_provider_health_snapshot(conn, _snapshot("manual", "failed", coverage_count=None))

    overview = load_data_quality_overview(conn)

    assert overview.provider_count == 3
    assert overview.stale_provider_count == 1
    assert overview.failed_provider_count == 1
    assert overview.restricted_provider_count == 2
    assert overview.total_coverage_count == 5
