from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb
from packages.core.fundamentals.models import build_fundamental_snapshot
from packages.core.fundamentals.repo import (
    get_latest_fundamental_snapshot,
    list_fundamental_snapshots,
    upsert_fundamental_snapshot,
)
from scripts.migrate import applied_versions, apply_migration, discover_migrations

NOW = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)


def test_upsert_and_get_latest_fundamental_snapshot(tmp_path: Path) -> None:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        _migrate(conn)
        older = build_fundamental_snapshot(
            symbol="BBCA",
            period="2025Q4",
            source="manual",
            source_type="manual",
            data_fields={"market_cap": 1},
            required_fields=["market_cap", "pe_ratio"],
            coverage_tier="tier_b",
            freshness_state="delayed",
            provider_trust_tier="tier_3",
            fetched_at=NOW.replace(hour=8),
            imported_at=NOW.replace(hour=8),
        )
        latest = build_fundamental_snapshot(
            symbol="BBCA",
            period="2026Q1",
            source="manual",
            source_type="manual",
            data_fields={"market_cap": 1, "pe_ratio": 12},
            required_fields=["market_cap", "pe_ratio"],
            coverage_tier="tier_a",
            freshness_state="fresh",
            provider_trust_tier="tier_2",
            fetched_at=NOW,
            imported_at=NOW,
        )

        assert upsert_fundamental_snapshot(conn, older) == 1
        assert upsert_fundamental_snapshot(conn, latest) == 1

        loaded = get_latest_fundamental_snapshot(conn, "bbca")
        assert loaded is not None
        assert loaded.period == "2026Q1"
        assert loaded.completeness_state == "complete"
        assert loaded.data_fields["pe_ratio"] == 12
        assert len(list_fundamental_snapshots(conn, symbol="BBCA")) == 2


def _migrate(conn: duckdb.DuckDBPyConnection) -> None:
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
