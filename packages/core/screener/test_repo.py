from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb
from packages.core.screener import ScreenerCandidate, ScreenerCondition, ScreenerRule
from packages.core.screener.evaluator import evaluate_screener_rule
from packages.core.screener.repo import (
    get_screener_rule,
    list_screener_results,
    upsert_screener_rule,
    upsert_screener_run,
)
from packages.core.ticker_coverage.models import SourceCoverageSnapshot, classify_ticker_coverage
from scripts.migrate import applied_versions, apply_migration, discover_migrations

NOW = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)


def test_upsert_rule_and_run_results_round_trip(tmp_path: Path) -> None:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        _migrate(conn)
        rule = ScreenerRule(
            rule_id="fundamentals-basic",
            name="Fundamental completeness filter",
            description="Filters symbols with visible coverage and fundamental fields.",
            required_fields=["market_cap"],
            required_source_types=["ohlcv"],
            min_coverage_tier="tier_b",
            conditions=[
                ScreenerCondition(
                    condition_id="market-cap-exists",
                    field_name="market_cap",
                    operator="exists",
                )
            ],
            created_at=NOW,
            updated_at=NOW,
        )
        coverage = classify_ticker_coverage(
            symbol="BBCA",
            lifecycle_status="active",
            ohlcv_available=True,
            ohlcv_freshness_state="fresh",
            provider_health_visible=True,
            fundamental_completeness="partial",
            source="manual",
            checked_at=NOW,
        )
        run = evaluate_screener_rule(
            rule,
            [
                ScreenerCandidate(
                    symbol="BBCA",
                    coverage=coverage,
                    source_coverage=[
                        SourceCoverageSnapshot(
                            symbol="BBCA",
                            provider_name="yfinance",
                            source_type="ohlcv",
                            provider_trust_tier="tier_3",
                            availability_state="available",
                            freshness_state="fresh",
                            last_checked_at=NOW,
                        )
                    ],
                    price_fields={"market_cap": 1},
                )
            ],
            run_id="run-1",
            evaluated_at=NOW,
        )

        assert upsert_screener_rule(conn, rule) == 1
        assert get_screener_rule(conn, "fundamentals-basic") == rule
        assert upsert_screener_run(conn, run) == 1

        results = list_screener_results(conn, run_id="run-1")

    assert len(results) == 1
    assert results[0].symbol == "BBCA.JK"
    assert results[0].result_status == "included"


def _migrate(conn: duckdb.DuckDBPyConnection) -> None:
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
