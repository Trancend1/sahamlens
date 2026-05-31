"""DuckDB persistence for provider health snapshots."""

from __future__ import annotations

from datetime import datetime

import duckdb
from packages.core.data_quality.models import DataQualityOverview, ProviderHealthSnapshot


def upsert_provider_health_snapshot(
    conn: duckdb.DuckDBPyConnection,
    snapshot: ProviderHealthSnapshot,
) -> int:
    """Idempotently store a provider health snapshot. Returns count written."""
    conn.execute(
        """
        INSERT INTO provider_health
            (provider_name, provider_trust_tier, source_type, freshness_state, updated_at,
             last_success_at, last_failure_at, last_failure_reason,
             consecutive_failure_count, coverage_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (provider_name, source_type) DO UPDATE SET
            provider_trust_tier = EXCLUDED.provider_trust_tier,
            freshness_state = EXCLUDED.freshness_state,
            updated_at = EXCLUDED.updated_at,
            last_success_at = EXCLUDED.last_success_at,
            last_failure_at = EXCLUDED.last_failure_at,
            last_failure_reason = EXCLUDED.last_failure_reason,
            consecutive_failure_count = EXCLUDED.consecutive_failure_count,
            coverage_count = EXCLUDED.coverage_count
        """,
        [
            snapshot.provider_name,
            snapshot.provider_trust_tier,
            snapshot.source_type,
            snapshot.freshness_state,
            snapshot.updated_at.isoformat(),
            snapshot.last_success_at.isoformat() if snapshot.last_success_at else None,
            snapshot.last_failure_at.isoformat() if snapshot.last_failure_at else None,
            snapshot.last_failure_reason,
            snapshot.consecutive_failure_count,
            snapshot.coverage_count,
        ],
    )
    return 1


def list_provider_health_snapshots(
    conn: duckdb.DuckDBPyConnection,
) -> list[ProviderHealthSnapshot]:
    rows = conn.execute(
        """
        SELECT provider_name, provider_trust_tier, source_type, freshness_state, updated_at,
               last_success_at, last_failure_at, last_failure_reason,
               consecutive_failure_count, coverage_count
        FROM provider_health
        ORDER BY provider_name, source_type
        """
    ).fetchall()
    return [_row_to_snapshot(row) for row in rows]


def load_data_quality_overview(conn: duckdb.DuckDBPyConnection) -> DataQualityOverview:
    return DataQualityOverview(providers=list_provider_health_snapshots(conn))


def _row_to_snapshot(row: tuple[object, ...]) -> ProviderHealthSnapshot:
    return ProviderHealthSnapshot.model_validate(
        {
            "provider_name": str(row[0]),
            "provider_trust_tier": str(row[1]),
            "source_type": str(row[2]),
            "freshness_state": str(row[3]),
            "updated_at": datetime.fromisoformat(str(row[4])),
            "last_success_at": _parse_optional_datetime(row[5]),
            "last_failure_at": _parse_optional_datetime(row[6]),
            "last_failure_reason": str(row[7]) if row[7] is not None else None,
            "consecutive_failure_count": int(str(row[8])),
            "coverage_count": int(str(row[9])) if row[9] is not None else None,
        }
    )


def _parse_optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(str(value))
