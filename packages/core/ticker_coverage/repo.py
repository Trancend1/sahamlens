"""DuckDB persistence for ticker lifecycle and source coverage."""

from __future__ import annotations

from datetime import datetime

import duckdb
from packages.core.data_sources.normalize import normalize_ticker
from packages.core.ticker_coverage.models import SourceCoverageSnapshot, TickerLifecycleSnapshot


def upsert_ticker_lifecycle_snapshot(
    conn: duckdb.DuckDBPyConnection,
    snapshot: TickerLifecycleSnapshot,
) -> int:
    conn.execute(
        """
        INSERT INTO ticker_lifecycle
            (symbol, lifecycle_status, coverage_tier, lifecycle_source, coverage_source,
             last_verified_at, renamed_from, renamed_to, missing_data_reason,
             screener_eligible, alert_eligible, ai_explanation_eligible,
             eligibility_reason, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol) DO UPDATE SET
            lifecycle_status = EXCLUDED.lifecycle_status,
            coverage_tier = EXCLUDED.coverage_tier,
            lifecycle_source = EXCLUDED.lifecycle_source,
            coverage_source = EXCLUDED.coverage_source,
            last_verified_at = EXCLUDED.last_verified_at,
            renamed_from = EXCLUDED.renamed_from,
            renamed_to = EXCLUDED.renamed_to,
            missing_data_reason = EXCLUDED.missing_data_reason,
            screener_eligible = EXCLUDED.screener_eligible,
            alert_eligible = EXCLUDED.alert_eligible,
            ai_explanation_eligible = EXCLUDED.ai_explanation_eligible,
            eligibility_reason = EXCLUDED.eligibility_reason,
            updated_at = EXCLUDED.updated_at
        """,
        [
            snapshot.symbol,
            snapshot.lifecycle_status,
            snapshot.coverage_tier,
            snapshot.lifecycle_source,
            snapshot.coverage_source,
            snapshot.last_verified_at.isoformat(),
            snapshot.renamed_from,
            snapshot.renamed_to,
            snapshot.missing_data_reason,
            int(snapshot.screener_eligible),
            int(snapshot.alert_eligible),
            int(snapshot.ai_explanation_eligible),
            snapshot.eligibility_reason,
            snapshot.updated_at.isoformat(),
        ],
    )
    return 1


def upsert_source_coverage_snapshot(
    conn: duckdb.DuckDBPyConnection,
    snapshot: SourceCoverageSnapshot,
) -> int:
    conn.execute(
        """
        INSERT INTO source_coverage
            (symbol, provider_name, source_type, provider_trust_tier, availability_state,
             freshness_state, last_success_at, last_checked_at, missing_reason, coverage_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol, provider_name, source_type) DO UPDATE SET
            provider_trust_tier = EXCLUDED.provider_trust_tier,
            availability_state = EXCLUDED.availability_state,
            freshness_state = EXCLUDED.freshness_state,
            last_success_at = EXCLUDED.last_success_at,
            last_checked_at = EXCLUDED.last_checked_at,
            missing_reason = EXCLUDED.missing_reason,
            coverage_count = EXCLUDED.coverage_count
        """,
        [
            snapshot.symbol,
            snapshot.provider_name,
            snapshot.source_type,
            snapshot.provider_trust_tier,
            snapshot.availability_state,
            snapshot.freshness_state,
            snapshot.last_success_at.isoformat() if snapshot.last_success_at else None,
            snapshot.last_checked_at.isoformat(),
            snapshot.missing_reason,
            snapshot.coverage_count,
        ],
    )
    return 1


def get_ticker_lifecycle_snapshot(
    conn: duckdb.DuckDBPyConnection,
    symbol: str,
) -> TickerLifecycleSnapshot | None:
    row = conn.execute(
        """
        SELECT symbol, lifecycle_status, coverage_tier, lifecycle_source, coverage_source,
               last_verified_at, renamed_from, renamed_to, missing_data_reason,
               screener_eligible, alert_eligible, ai_explanation_eligible,
               eligibility_reason, updated_at
        FROM ticker_lifecycle
        WHERE symbol = ?
        """,
        [normalize_ticker(symbol)],
    ).fetchone()
    return _row_to_lifecycle(row) if row else None


def list_ticker_lifecycle_snapshots(
    conn: duckdb.DuckDBPyConnection,
) -> list[TickerLifecycleSnapshot]:
    rows = conn.execute(
        """
        SELECT symbol, lifecycle_status, coverage_tier, lifecycle_source, coverage_source,
               last_verified_at, renamed_from, renamed_to, missing_data_reason,
               screener_eligible, alert_eligible, ai_explanation_eligible,
               eligibility_reason, updated_at
        FROM ticker_lifecycle
        ORDER BY symbol
        """
    ).fetchall()
    return [_row_to_lifecycle(row) for row in rows]


def list_source_coverage_snapshots(
    conn: duckdb.DuckDBPyConnection,
) -> list[SourceCoverageSnapshot]:
    rows = conn.execute(
        """
        SELECT symbol, provider_name, source_type, provider_trust_tier, availability_state,
               freshness_state, last_success_at, last_checked_at, missing_reason, coverage_count
        FROM source_coverage
        ORDER BY symbol, provider_name, source_type
        """
    ).fetchall()
    return [_row_to_source_coverage(row) for row in rows]


def _row_to_lifecycle(row: tuple[object, ...]) -> TickerLifecycleSnapshot:
    return TickerLifecycleSnapshot.model_validate(
        {
            "symbol": str(row[0]),
            "lifecycle_status": str(row[1]),
            "coverage_tier": str(row[2]),
            "lifecycle_source": str(row[3]),
            "coverage_source": str(row[4]),
            "last_verified_at": datetime.fromisoformat(str(row[5])),
            "renamed_from": _optional_str(row[6]),
            "renamed_to": _optional_str(row[7]),
            "missing_data_reason": _optional_str(row[8]),
            "screener_eligible": bool(row[9]),
            "alert_eligible": bool(row[10]),
            "ai_explanation_eligible": bool(row[11]),
            "eligibility_reason": _optional_str(row[12]),
            "updated_at": datetime.fromisoformat(str(row[13])),
        }
    )


def _row_to_source_coverage(row: tuple[object, ...]) -> SourceCoverageSnapshot:
    return SourceCoverageSnapshot.model_validate(
        {
            "symbol": str(row[0]),
            "provider_name": str(row[1]),
            "source_type": str(row[2]),
            "provider_trust_tier": str(row[3]),
            "availability_state": str(row[4]),
            "freshness_state": str(row[5]),
            "last_success_at": _optional_datetime(row[6]),
            "last_checked_at": datetime.fromisoformat(str(row[7])),
            "missing_reason": _optional_str(row[8]),
            "coverage_count": int(str(row[9])) if row[9] is not None else None,
        }
    )


def _optional_datetime(value: object) -> datetime | None:
    return datetime.fromisoformat(str(value)) if value is not None else None


def _optional_str(value: object) -> str | None:
    return str(value) if value is not None else None
