from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from _pytest.capture import CaptureFixture
from packages.core.fundamentals import upsert_fundamental_snapshot
from packages.core.fundamentals.models import build_fundamental_snapshot
from packages.core.screener.repo import list_screener_results
from packages.core.ticker_coverage import (
    SourceCoverageSnapshot,
    classify_ticker_coverage,
    upsert_source_coverage_snapshot,
    upsert_ticker_lifecycle_snapshot,
)

from scripts import screener
from scripts.migrate import applied_versions, apply_migration, discover_migrations

NOW = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)


def test_screener_cli_runs_builtin_rule_and_persists_results(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    db = tmp_path / "test.duckdb"
    with duckdb.connect(str(db)) as conn:
        _migrate(conn)
        _seed_symbol(conn, "BBCA", fields={"market_cap": 1_000_000, "roe": 0.18})
        _seed_symbol(conn, "TLKM", ohlcv_available=False, fields={"market_cap": 1_000_000})
    capsys.readouterr()

    exit_code = screener.main(
        [
            "--db",
            str(db),
            "--json",
            "run",
            "--builtin",
            "fundamentals-basic",
            "--symbols",
            "BBCA,TLKM",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["rule"]["rule_id"] == "fundamentals-basic"
    assert output["included_count"] == 1
    assert output["excluded_count"] == 1
    assert [result["symbol"] for result in output["results"]] == ["BBCA.JK", "TLKM.JK"]
    assert output["results"][0]["result_status"] == "included"
    assert "excluded" in output["results"][1]["explanation"].lower()
    assert "buy" not in json.dumps(output).lower()
    with duckdb.connect(str(db)) as conn:
        persisted = list_screener_results(conn, run_id=output["run_id"])
    assert len(persisted) == 2


def _seed_symbol(
    conn: duckdb.DuckDBPyConnection,
    symbol: str,
    *,
    ohlcv_available: bool = True,
    fields: dict[str, object],
) -> None:
    source = SourceCoverageSnapshot(
        symbol=symbol,
        provider_name="yfinance",
        source_type="ohlcv",
        provider_trust_tier="tier_3",
        availability_state="available" if ohlcv_available else "missing",
        freshness_state="fresh" if ohlcv_available else "unknown",
        last_checked_at=NOW,
    )
    upsert_source_coverage_snapshot(conn, source)
    fundamental = build_fundamental_snapshot(
        symbol=symbol,
        period="2026Q1",
        source="manual",
        source_type="manual",
        data_fields=fields,
        required_fields=["market_cap", "roe"],
        coverage_tier="tier_b",
        freshness_state=source.freshness_state,
        provider_trust_tier="tier_3",
        fetched_at=NOW,
        imported_at=NOW,
    )
    upsert_fundamental_snapshot(conn, fundamental)
    lifecycle = classify_ticker_coverage(
        symbol=symbol,
        lifecycle_status="active",
        ohlcv_available=ohlcv_available,
        ohlcv_freshness_state=source.freshness_state,
        provider_health_visible=True,
        fundamental_completeness=fundamental.completeness_state,
        source="manual",
        checked_at=NOW,
    )
    upsert_ticker_lifecycle_snapshot(conn, lifecycle)


def _migrate(conn: duckdb.DuckDBPyConnection) -> None:
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
