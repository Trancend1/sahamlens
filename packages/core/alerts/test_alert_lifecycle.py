from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import duckdb
import pytest
from packages.core.alerts import (
    AlertRule,
    AlertRuleInput,
    acknowledge_alert_event,
    archive_alert_rule,
    create_alert_rule,
    dismiss_alert_event,
    evaluate_active_alert_rules,
    get_alert_event,
    list_alert_events,
    list_alert_rules,
    mark_alert_event_false_positive,
    pause_alert_rule,
)
from packages.core.data_quality.models import FreshnessState
from packages.core.fundamentals import build_fundamental_snapshot, upsert_fundamental_snapshot
from packages.core.schemas.models import PriceRow
from packages.core.schemas.repository import upsert_price_rows
from packages.core.ticker_coverage import SourceCoverageSnapshot, upsert_source_coverage_snapshot
from scripts.migrate import applied_versions, apply_migration, discover_migrations

NOW = datetime(2026, 6, 5, 9, 0, tzinfo=UTC)


def test_alert_rule_crud_rejects_invalid_type_and_parameters(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        rule = create_alert_rule(
            conn,
            AlertRuleInput(
                name="BBCA price check",
                description="Checks whether local close is above a threshold.",
                rule_type="price_above",
                ticker="BBCA",
                parameters={"threshold": 9000},
                now=NOW,
            ),
        )

        assert rule.id
        assert rule.ticker == "BBCA.JK"
        assert rule.definition_status == "active"
        assert list_alert_rules(conn) == [rule]

        paused = pause_alert_rule(conn, rule.id, now=NOW)
        assert paused is not None
        assert paused.definition_status == "paused"

        archived = archive_alert_rule(conn, rule.id, now=NOW)
        assert archived is not None
        assert archived.definition_status == "archived"

        with pytest.raises(ValueError, match="unsupported alert rule type"):
            AlertRuleInput(
                name="Bad rule",
                description="Bad rule",
                rule_type=cast(Any, "prediction"),
                ticker="BBCA",
                parameters={"threshold": 1},
                now=NOW,
            )
        with pytest.raises(ValueError, match="threshold"):
            AlertRuleInput(
                name="Missing threshold",
                description="Missing threshold",
                rule_type="price_above",
                ticker="BBCA",
                parameters={},
                now=NOW,
            )


def test_matching_rule_creates_evaluation_and_event(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        _seed_symbol(conn, "BBCA", close=9500, volume=1_000_000)
        rule = create_alert_rule(
            conn,
            AlertRuleInput(
                name="BBCA above threshold",
                description="Checks whether close is above the configured threshold.",
                rule_type="price_above",
                ticker="BBCA",
                parameters={"threshold": 9000},
                now=NOW,
            ),
        )

        result = evaluate_active_alert_rules(conn, evaluated_at=NOW)

        assert result.evaluated_count == 1
        assert result.event_count == 1
        assert result.evaluations[0].rule_id == rule.id
        assert result.evaluations[0].status == "success"
        assert result.evaluations[0].matched is True
        assert result.events[0].status == "new"
        assert result.events[0].event_type == "price_above"
        assert list_alert_events(conn)[0] == result.events[0]


def test_no_match_creates_evaluation_without_event(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        _seed_symbol(conn, "BBCA", close=8500, volume=1_000_000)
        create_alert_rule(
            conn,
            AlertRuleInput(
                name="BBCA above threshold",
                description="Checks whether close is above the configured threshold.",
                rule_type="price_above",
                ticker="BBCA",
                parameters={"threshold": 9000},
                now=NOW,
            ),
        )

        result = evaluate_active_alert_rules(conn, evaluated_at=NOW)

        assert result.evaluated_count == 1
        assert result.event_count == 0
        assert result.evaluations[0].status == "no_match"
        assert result.evaluations[0].matched is False
        assert list_alert_events(conn) == []


def test_stale_or_low_confidence_skips_without_event(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        _seed_symbol(conn, "BBCA", close=9500, volume=1_000_000, freshness_state="stale")
        _seed_symbol(
            conn,
            "TLKM",
            close=4100,
            volume=1_000_000,
            confidence_fields={"market_cap": 1},
        )
        create_alert_rule(
            conn,
            AlertRuleInput(
                name="BBCA stale skip",
                description="Checks whether close is above the configured threshold.",
                rule_type="price_above",
                ticker="BBCA",
                parameters={"threshold": 9000},
                now=NOW,
            ),
        )
        create_alert_rule(
            conn,
            AlertRuleInput(
                name="TLKM low confidence skip",
                description="Checks whether close is above the configured threshold.",
                rule_type="price_above",
                ticker="TLKM",
                parameters={"threshold": 4000},
                now=NOW,
            ),
        )

        result = evaluate_active_alert_rules(conn, evaluated_at=NOW)

        statuses = {evaluation.ticker: evaluation.status for evaluation in result.evaluations}
        assert statuses == {
            "BBCA.JK": "skipped_stale_data",
            "TLKM.JK": "skipped_low_confidence",
        }
        assert result.event_count == 0
        assert list_alert_events(conn) == []


def test_event_lifecycle_transitions_are_idempotent(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        _seed_symbol(conn, "BBCA", close=9500, volume=1_000_000)
        create_alert_rule(
            conn,
            AlertRuleInput(
                name="BBCA above threshold",
                description="Checks whether close is above the configured threshold.",
                rule_type="price_above",
                ticker="BBCA",
                parameters={"threshold": 9000},
                now=NOW,
            ),
        )
        event = evaluate_active_alert_rules(conn, evaluated_at=NOW).events[0]

        acknowledged = acknowledge_alert_event(conn, event.id, now=NOW)
        dismissed = dismiss_alert_event(conn, event.id, now=NOW)
        false_positive = mark_alert_event_false_positive(
            conn,
            event.id,
            notes="Repeated known condition.",
            now=NOW,
        )
        repeated_false_positive = mark_alert_event_false_positive(
            conn,
            event.id,
            notes="Do not duplicate.",
            now=NOW,
        )

        assert acknowledged is not None
        assert acknowledged.status == "acknowledged"
        assert dismissed is not None
        assert dismissed.status == "dismissed"
        assert false_positive is not None
        assert false_positive.status == "marked_false_positive"
        assert false_positive.false_positive_at == NOW
        assert repeated_false_positive == false_positive
        assert get_alert_event(conn, event.id) == false_positive


def test_paused_and_archived_rules_are_not_evaluated(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        _seed_symbol(conn, "BBCA", close=9500, volume=1_000_000)
        paused_rule = create_alert_rule(
            conn,
            AlertRuleInput(
                name="Paused rule",
                description="Should not evaluate.",
                rule_type="price_above",
                ticker="BBCA",
                parameters={"threshold": 9000},
                now=NOW,
            ),
        )
        archived_rule = create_alert_rule(
            conn,
            AlertRuleInput(
                name="Archived rule",
                description="Should not evaluate.",
                rule_type="price_above",
                ticker="BBCA",
                parameters={"threshold": 9000},
                now=NOW,
            ),
        )
        pause_alert_rule(conn, paused_rule.id, now=NOW)
        archive_alert_rule(conn, archived_rule.id, now=NOW)

        result = evaluate_active_alert_rules(conn, evaluated_at=NOW)

        assert result.evaluated_count == 0
        assert result.event_count == 0


def test_alert_rule_round_trip_model(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        rule = create_alert_rule(
            conn,
            AlertRuleInput(
                name="Volume check",
                description="Checks volume threshold.",
                rule_type="volume_above",
                ticker="BBCA",
                parameters={"threshold": 1_000_000},
                now=NOW,
            ),
        )

        assert isinstance(rule, AlertRule)
        assert list_alert_rules(conn)[0].parameters == {"threshold": 1_000_000}


def _db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "alerts.duckdb"))
    _migrate(conn)
    return conn


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
    freshness_state: str = "fresh",
    confidence_fields: dict[str, object] | None = None,
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
            freshness_state=cast(FreshnessState, freshness_state),
            last_success_at=NOW if freshness_state != "failed" else None,
            last_checked_at=NOW,
        ),
    )
    fields = confidence_fields or {"market_cap": 1_000_000, "roe": 0.18}
    snapshot = build_fundamental_snapshot(
        symbol=symbol,
        period="2026Q1",
        source="manual",
        source_type="manual",
        data_fields=fields,
        required_fields=["market_cap", "roe"],
        coverage_tier="tier_a",
        freshness_state=cast(FreshnessState, freshness_state),
        provider_trust_tier="tier_2",
        fetched_at=NOW,
        imported_at=NOW,
    )
    upsert_fundamental_snapshot(conn, snapshot)
