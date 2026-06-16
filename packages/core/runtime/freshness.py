"""Data freshness tracker.

Queries existing DuckDB timestamps to classify data freshness
per domain. No new DB table — reads from existing TEXT columns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

import duckdb

DataFreshnessStatus = Literal["fresh", "stale", "unknown"]

# Threshold per data type — data older than this is "stale"
DEFAULT_THRESHOLDS: dict[str, timedelta] = {
    "alerts": timedelta(hours=1),
    "news": timedelta(hours=6),
    "provider_health": timedelta(hours=6),
    "prices": timedelta(days=1),
    "ticker_coverage": timedelta(days=1),
    "screener": timedelta(days=1),
    "strategy_rules": timedelta(days=1),
    "fundamentals": timedelta(days=7),
    "weekly_review": timedelta(days=7),
}

# Table → MAX(column) queries per data type
FRESHNESS_QUERIES: dict[str, tuple[str, str]] = {
    "provider_health": ("provider_health", "SELECT MAX(updated_at) FROM provider_health"),
    "prices": ("price_history", "SELECT MAX(fetched_at) FROM price_history"),
    "fundamentals": ("fundamental_snapshots", "SELECT MAX(fetched_at) FROM fundamental_snapshots"),
    "ticker_coverage": ("source_coverage", "SELECT MAX(last_checked_at) FROM source_coverage"),
    "news": ("news", "SELECT MAX(fetched_at) FROM news"),
    "alerts": ("alert_evaluations", "SELECT MAX(evaluated_at) FROM alert_evaluations"),
    "screener": ("screener_results", "SELECT MAX(evaluated_at) FROM screener_results"),
    "strategy_rules": (
        "strategy_rule_evaluations",
        "SELECT MAX(evaluated_at) FROM strategy_rule_evaluations",
    ),
    "weekly_review": ("weekly_review_runs", "SELECT MAX(generated_at) FROM weekly_review_runs"),
}


@dataclass
class FreshnessRecord:
    data_type: str
    status: DataFreshnessStatus
    last_refreshed_at: str | None
    age_seconds: float | None
    threshold_seconds: int


@dataclass
class FreshnessReport:
    records: list[FreshnessRecord] = field(default_factory=list)

    @property
    def has_stale(self) -> bool:
        return any(r.status == "stale" for r in self.records)

    @property
    def stale_count(self) -> int:
        return sum(1 for r in self.records if r.status == "stale")

    @property
    def fresh_count(self) -> int:
        return sum(1 for r in self.records if r.status == "fresh")

    @property
    def total_count(self) -> int:
        return len(self.records)

    @property
    def stale_types(self) -> list[str]:
        return [r.data_type for r in self.records if r.status == "stale"]


def _parse_iso(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
    return None


def check_freshness(db_path: str) -> FreshnessReport:
    resolved = Path(db_path).resolve()
    if not resolved.exists():
        return FreshnessReport()

    now = datetime.now(UTC)
    records: list[FreshnessRecord] = []

    with duckdb.connect(str(resolved), read_only=True) as conn:
        tables = {str(row[0]) for row in conn.execute("SHOW TABLES").fetchall()}

        for data_type, (table_name, query) in FRESHNESS_QUERIES.items():
            threshold = DEFAULT_THRESHOLDS.get(data_type, timedelta(days=1))
            if table_name not in tables:
                records.append(
                    FreshnessRecord(
                        data_type=data_type,
                        status="unknown",
                        last_refreshed_at=None,
                        age_seconds=None,
                        threshold_seconds=int(threshold.total_seconds()),
                    )
                )
                continue

            row = conn.execute(query).fetchone()
            raw = row[0] if row else None
            dt = _parse_iso(raw)

            if dt is None:
                records.append(
                    FreshnessRecord(
                        data_type=data_type,
                        status="unknown",
                        last_refreshed_at=None,
                        age_seconds=None,
                        threshold_seconds=int(threshold.total_seconds()),
                    )
                )
                continue

            age = now - dt
            status: DataFreshnessStatus = "fresh" if age <= threshold else "stale"
            records.append(
                FreshnessRecord(
                    data_type=data_type,
                    status=status,
                    last_refreshed_at=dt.isoformat(),
                    age_seconds=age.total_seconds(),
                    threshold_seconds=int(threshold.total_seconds()),
                )
            )

    return FreshnessReport(records=records)
