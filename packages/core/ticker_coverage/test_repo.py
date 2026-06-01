from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb
from packages.core.ticker_coverage.models import SourceCoverageSnapshot, classify_ticker_coverage
from packages.core.ticker_coverage.repo import (
    get_ticker_lifecycle_snapshot,
    list_ticker_lifecycle_snapshots,
    upsert_source_coverage_snapshot,
    upsert_ticker_lifecycle_snapshot,
)
from scripts.migrate import applied_versions, apply_migration, discover_migrations

NOW = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)


def test_upsert_and_list_ticker_lifecycle_snapshot(tmp_path: Path) -> None:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        _migrate(conn)
        snapshot = classify_ticker_coverage(
            symbol="BBCA",
            lifecycle_status="active",
            ohlcv_available=True,
            ohlcv_freshness_state="fresh",
            provider_health_visible=True,
            fundamental_completeness="partial",
            source="manual",
            checked_at=NOW,
        )

        assert upsert_ticker_lifecycle_snapshot(conn, snapshot) == 1
        assert upsert_ticker_lifecycle_snapshot(conn, snapshot) == 1

        loaded = get_ticker_lifecycle_snapshot(conn, "bbca")
        assert loaded is not None
        assert loaded.symbol == "BBCA.JK"
        assert loaded.coverage_tier == "tier_a"
        assert loaded.screener_eligible is True
        assert list_ticker_lifecycle_snapshots(conn)[0].symbol == "BBCA.JK"


def test_upsert_source_coverage_snapshot(tmp_path: Path) -> None:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        _migrate(conn)
        snapshot = SourceCoverageSnapshot(
            symbol="TLKM",
            provider_name="yfinance",
            source_type="ohlcv",
            provider_trust_tier="tier_3",
            availability_state="missing",
            freshness_state="unknown",
            last_checked_at=NOW,
            missing_reason="no price rows",
        )

        assert upsert_source_coverage_snapshot(conn, snapshot) == 1
        rows = conn.execute(
            "SELECT symbol, provider_name, source_type, availability_state FROM source_coverage"
        ).fetchall()

    assert rows == [("TLKM.JK", "yfinance", "ohlcv", "missing")]


def _migrate(conn: duckdb.DuckDBPyConnection) -> None:
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
