from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest
from packages.core.watchlist import add_entry
from scripts import fundamentals
from scripts.migrate import applied_versions, apply_migration, discover_migrations


@pytest.fixture
def db_path(tmp_path: Path) -> Iterator[Path]:
    db = tmp_path / "fundamentals.duckdb"
    with duckdb.connect(str(db)) as conn:
        applied_versions(conn)
        for path in discover_migrations():
            apply_migration(conn, path)
        add_entry(conn, "BBCA", tag="bank")
    yield db


def test_ingest_and_list_fundamental_snapshot_json(
    db_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = fundamentals.main(
        [
            "--db",
            str(db_path),
            "--json",
            "ingest",
            "--symbol",
            "BBCA",
            "--period",
            "2026Q1",
            "--field",
            "market_cap=1000",
            "--field",
            "roe=0.18",
            "--required-fields",
            "market_cap,pe_ratio,pbv,roe",
        ]
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["symbol"] == "BBCA.JK"
    assert payload["completeness_state"] == "partial"
    assert payload["missing_fields"] == ["pe_ratio", "pbv"]

    rc = fundamentals.main(["--db", str(db_path), "--json", "list", "--symbol", "bbca"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload) == 1
    assert payload[0]["period"] == "2026Q1"


def test_refresh_coverage_for_watchlist_is_conservative_without_price_rows(
    db_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = fundamentals.main(
        [
            "--db",
            str(db_path),
            "--json",
            "refresh-coverage",
            "--from-watchlist",
            "--lifecycle-status",
            "active",
        ]
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["symbol"] == "BBCA.JK"
    assert payload[0]["coverage_tier"] == "tier_c"
    assert payload[0]["screener_eligible"] is False
    assert "provider health" in payload[0]["eligibility_reason"]


def test_snapshot_command_combines_coverage_and_latest_fundamental(
    db_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fundamentals.main(
        [
            "--db",
            str(db_path),
            "--json",
            "ingest",
            "--symbol",
            "BBCA",
            "--period",
            "2026Q1",
            "--field",
            "market_cap=1000",
        ]
    )
    capsys.readouterr()
    rc = fundamentals.main(["--db", str(db_path), "--json", "snapshot", "--symbol", "BBCA"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["symbol"] == "BBCA.JK"
    assert payload["fundamental"]["symbol"] == "BBCA.JK"
    assert payload["coverage"] is None
