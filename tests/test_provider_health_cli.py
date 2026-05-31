"""Tests for provider health refresh/list CLI behavior."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb
import pytest
from packages.core.schemas.models import FetchResult, FetchStatus, PriceRow
from scripts import provider_health
from scripts.migrate import applied_versions, apply_migration, discover_migrations


class FakeSource:
    name = "fake-yfinance"

    def __init__(self, results: dict[str, FetchResult]) -> None:
        self.results = results

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> FetchResult:
        return self.results[symbol]


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


@pytest.fixture
def db_path(tmp_path: Path) -> Iterator[Path]:
    db = tmp_path / "provider-health.duckdb"
    with duckdb.connect(str(db)) as c:
        applied_versions(c)
        for path in discover_migrations():
            apply_migration(c, path)
    yield db


def _result(symbol: str, status: FetchStatus) -> FetchResult:
    fetched_at = datetime(2026, 5, 31, 9, 0, tzinfo=UTC)
    rows: list[PriceRow] = []
    if status == "ok":
        rows = [
            PriceRow(
                symbol=symbol,
                date=date(2026, 5, 30),
                open=1.0,
                high=1.0,
                low=1.0,
                close=1.0,
                volume=1,
                source="fake-yfinance",
                fetched_at=fetched_at,
            )
        ]
    return FetchResult(
        symbol=symbol,
        source="fake-yfinance",
        fetched_at=fetched_at,
        status=status,
        rows=rows,
        error_message="boom" if status == "failed" else None,
    )


def test_build_yfinance_snapshot_maps_ok_results_to_fresh(conn: duckdb.DuckDBPyConnection) -> None:
    source = FakeSource({"BBCA.JK": _result("BBCA.JK", "ok")})

    snapshot = provider_health.refresh_yfinance_provider_health(
        conn,
        source,
        ["BBCA.JK"],
        start=date(2026, 5, 1),
        end=date(2026, 5, 31),
    )

    assert snapshot.provider_name == "fake-yfinance"
    assert snapshot.freshness_state == "fresh"
    assert snapshot.last_success_at == datetime(2026, 5, 31, 9, 0, tzinfo=UTC)
    assert snapshot.coverage_count == 1


def test_build_yfinance_snapshot_maps_partial_results_to_partial(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    source = FakeSource({"BBCA.JK": _result("BBCA.JK", "partial")})

    snapshot = provider_health.refresh_yfinance_provider_health(
        conn,
        source,
        ["BBCA.JK"],
        start=date(2026, 5, 1),
        end=date(2026, 5, 31),
    )

    assert snapshot.freshness_state == "partial"
    assert snapshot.coverage_count == 0


def test_build_yfinance_snapshot_maps_failed_results_to_failed(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    source = FakeSource({"BBCA.JK": _result("BBCA.JK", "failed")})

    snapshot = provider_health.refresh_yfinance_provider_health(
        conn,
        source,
        ["BBCA.JK"],
        start=date(2026, 5, 1),
        end=date(2026, 5, 31),
    )

    assert snapshot.freshness_state == "failed"
    assert snapshot.last_failure_at == datetime(2026, 5, 31, 9, 0, tzinfo=UTC)
    assert snapshot.last_failure_reason == "BBCA.JK: boom"
    assert snapshot.consecutive_failure_count == 1


def test_list_command_emits_overview_json(
    db_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = provider_health.main(["--db", str(db_path), "--json", "list"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["provider_count"] == 0
    assert payload["providers"] == []
