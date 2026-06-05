from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest
from packages.core.fundamentals import build_fundamental_snapshot, upsert_fundamental_snapshot
from packages.core.schemas.models import PriceRow
from packages.core.schemas.repository import upsert_price_rows
from packages.core.ticker_coverage import SourceCoverageSnapshot, upsert_source_coverage_snapshot

from scripts import alerts
from scripts.migrate import applied_versions, apply_migration, discover_migrations

NOW = datetime(2026, 6, 5, 9, 0, tzinfo=UTC)


def test_alerts_cli_rule_evaluate_and_event_lifecycle_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = tmp_path / "alerts.duckdb"
    with duckdb.connect(str(db)) as conn:
        _migrate(conn)
        _seed_symbol(conn, "BBCA", close=9500, volume=1_000_000)
    capsys.readouterr()

    create_exit = alerts.main(
        [
            "--db",
            str(db),
            "--json",
            "rules",
            "create",
            "--name",
            "BBCA threshold review",
            "--rule-type",
            "price_above",
            "--ticker",
            "BBCA",
            "--params",
            '{"threshold":9000}',
        ]
    )
    created = json.loads(capsys.readouterr().out)
    eval_exit = alerts.main(["--db", str(db), "--json", "evaluate"])
    evaluated = json.loads(capsys.readouterr().out)
    list_exit = alerts.main(["--db", str(db), "--json", "events", "list"])
    events = json.loads(capsys.readouterr().out)
    event_id = events["items"][0]["id"]
    false_positive_exit = alerts.main(
        [
            "--db",
            str(db),
            "--json",
            "events",
            "mark-false-positive",
            "--event-id",
            event_id,
        ]
    )
    false_positive = json.loads(capsys.readouterr().out)

    assert create_exit == 0
    assert eval_exit == 0
    assert list_exit == 0
    assert false_positive_exit == 0
    assert created["ok"] is True
    assert created["item"]["ticker"] == "BBCA.JK"
    assert evaluated["ok"] is True
    assert evaluated["item"]["event_count"] == 1
    assert events["items"][0]["status"] == "new"
    assert false_positive["item"]["status"] == "marked_false_positive"
    combined = json.dumps([created, evaluated, events, false_positive])
    assert "Traceback" not in combined
    assert "buy signal" not in combined.lower()


def test_alerts_cli_missing_schema_returns_structured_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = tmp_path / "stale.duckdb"
    with duckdb.connect(str(db)) as conn:
        for migration in discover_migrations()[:6]:
            apply_migration(conn, migration)
    capsys.readouterr()

    exit_code = alerts.main(["--db", str(db), "--json", "rules", "list"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert payload["ok"] is False
    assert payload["status"] == "schema_stale"
    assert payload["errors"][0]["code"] in {"schema_stale", "missing_table"}
    assert "uv run python -m scripts.migrate" in payload["recommended_commands"]
    assert "Traceback" not in json.dumps(payload)


def test_alerts_cli_telegram_status_is_safe_without_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("SAHAMLENS_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("SAHAMLENS_TELEGRAM_CHAT_ID", raising=False)

    exit_code = alerts.main(["--json", "telegram", "status"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["status"] == "not_configured"
    assert payload["item"]["enabled"] is False
    assert payload["item"]["bot_token_configured"] is False
    assert payload["item"]["chat_id_configured"] is False
    assert "Traceback" not in json.dumps(payload)


def test_alerts_cli_telegram_send_not_configured_records_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("SAHAMLENS_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("SAHAMLENS_TELEGRAM_CHAT_ID", raising=False)
    db = tmp_path / "alerts.duckdb"
    with duckdb.connect(str(db)) as conn:
        _migrate(conn)
        _seed_symbol(conn, "BBCA", close=9500, volume=1_000_000)
    capsys.readouterr()

    alerts.main(
        [
            "--db",
            str(db),
            "--json",
            "rules",
            "create",
            "--name",
            "BBCA threshold review",
            "--rule-type",
            "price_above",
            "--ticker",
            "BBCA",
            "--params",
            '{"threshold":9000}',
        ]
    )
    capsys.readouterr()
    alerts.main(["--db", str(db), "--json", "evaluate"])
    evaluated = json.loads(capsys.readouterr().out)
    event_id = evaluated["item"]["events"][0]["id"]

    exit_code = alerts.main(["--db", str(db), "--json", "telegram", "send", "--event-id", event_id])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["status"] == "skipped_not_configured"
    assert payload["item"]["status"] == "skipped_not_configured"
    assert "Traceback" not in json.dumps(payload)


def _migrate(conn: duckdb.DuckDBPyConnection) -> None:
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)


def _seed_symbol(
    conn: duckdb.DuckDBPyConnection,
    symbol: str,
    *,
    close: float,
    volume: int,
) -> None:
    upsert_price_rows(
        conn,
        [
            PriceRow(
                symbol=symbol,
                date=NOW.date(),
                open=close - 100,
                high=close + 100,
                low=close - 200,
                close=close,
                volume=volume,
                source="manual",
                fetched_at=NOW,
            )
        ],
    )
    upsert_source_coverage_snapshot(
        conn,
        SourceCoverageSnapshot(
            symbol=symbol,
            provider_name="manual",
            source_type="ohlcv",
            provider_trust_tier="tier_2",
            availability_state="available",
            freshness_state="fresh",
            last_success_at=NOW,
            last_checked_at=NOW,
        ),
    )
    snapshot = build_fundamental_snapshot(
        symbol=symbol,
        period="2026Q1",
        source="manual",
        source_type="manual",
        data_fields={"market_cap": 1_000_000, "roe": 0.18},
        required_fields=["market_cap", "roe"],
        coverage_tier="tier_a",
        freshness_state="fresh",
        provider_trust_tier="tier_2",
        fetched_at=NOW,
        imported_at=NOW,
    )
    upsert_fundamental_snapshot(conn, snapshot)
