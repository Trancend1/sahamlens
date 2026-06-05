from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from packages.core.alerts import (
    AlertEvaluation,
    AlertEvent,
    AlertRuleInput,
    create_alert_rule,
    get_alert_event,
    insert_alert_evaluation,
    insert_alert_event,
    list_alert_delivery_attempts,
)
from packages.core.alerts.telegram import (
    TelegramSendResponse,
    format_telegram_alert_message,
    get_telegram_status,
    send_alert_event_to_telegram,
)
from scripts.migrate import applied_versions, apply_migration, discover_migrations

NOW = datetime(2026, 6, 5, 10, 0, tzinfo=UTC)
BOT_SAMPLE_VALUE = "BOT_SAMPLE_VALUE"
CHAT_SAMPLE_VALUE = "CHAT_SAMPLE_VALUE"


def test_telegram_status_missing_config_is_disabled_without_secret_leak() -> None:
    status = get_telegram_status(env={})

    assert status.enabled is False
    assert status.status == "not_configured"
    assert status.bot_token_configured is False
    assert status.chat_id_configured is False


def test_telegram_status_configured_redacts_token_and_chat_id() -> None:
    status = get_telegram_status(
        env={
            "SAHAMLENS_TELEGRAM_BOT_TOKEN": BOT_SAMPLE_VALUE,
            "SAHAMLENS_TELEGRAM_CHAT_ID": CHAT_SAMPLE_VALUE,
        }
    )
    payload = json.dumps(status.model_dump(mode="json"))

    assert status.enabled is True
    assert status.status == "configured"
    assert status.bot_token_configured is True
    assert status.chat_id_configured is True
    assert BOT_SAMPLE_VALUE not in payload
    assert CHAT_SAMPLE_VALUE not in payload


def test_telegram_send_skipped_when_not_configured_records_attempt(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        event = _seed_event(conn)

        result = send_alert_event_to_telegram(conn, event.id, env={})
        attempts = list_alert_delivery_attempts(conn, event_id=event.id)

        assert result.ok is True
        assert result.status == "skipped_not_configured"
        assert attempts[0].status == "skipped_not_configured"
        assert get_alert_event(conn, event.id) == event


def test_telegram_send_success_records_attempt_without_secret_leak(tmp_path: Path) -> None:
    calls: list[tuple[str, str, str]] = []

    def transport(token: str, chat_id: str, text: str) -> TelegramSendResponse:
        calls.append((token, chat_id, text))
        return TelegramSendResponse(ok=True, status_code=200)

    with _db(tmp_path) as conn:
        event = _seed_event(conn)

        result = send_alert_event_to_telegram(
            conn,
            event.id,
            env={
                "SAHAMLENS_TELEGRAM_BOT_TOKEN": BOT_SAMPLE_VALUE,
                "SAHAMLENS_TELEGRAM_CHAT_ID": CHAT_SAMPLE_VALUE,
            },
            transport=transport,
        )
        attempts = list_alert_delivery_attempts(conn, event_id=event.id)
        payload = json.dumps(result.model_dump(mode="json"))

        assert result.ok is True
        assert result.status == "sent"
        assert attempts[0].status == "sent"
        assert calls[0][0] == BOT_SAMPLE_VALUE
        assert calls[0][1] == CHAT_SAMPLE_VALUE
        assert "SahamLens alert event" in calls[0][2]
        assert "Rule condition matched" in calls[0][2]
        assert BOT_SAMPLE_VALUE not in payload
        assert CHAT_SAMPLE_VALUE not in payload


def test_telegram_send_failure_records_attempt_and_keeps_event(tmp_path: Path) -> None:
    def transport(_token: str, _chat_id: str, _text: str) -> TelegramSendResponse:
        return TelegramSendResponse(
            ok=False,
            status_code=500,
            error_code="telegram_http_error",
            error_message="Telegram request failed.",
        )

    with _db(tmp_path) as conn:
        event = _seed_event(conn)

        result = send_alert_event_to_telegram(
            conn,
            event.id,
            env={
                "SAHAMLENS_TELEGRAM_BOT_TOKEN": BOT_SAMPLE_VALUE,
                "SAHAMLENS_TELEGRAM_CHAT_ID": CHAT_SAMPLE_VALUE,
            },
            transport=transport,
        )
        attempts = list_alert_delivery_attempts(conn, event_id=event.id)

        assert result.ok is False
        assert result.status == "failed"
        assert attempts[0].status == "failed"
        assert get_alert_event(conn, event.id) == event


def test_telegram_send_failure_redacts_reflected_secret_values(tmp_path: Path) -> None:
    def transport(token: str, chat_id: str, _text: str) -> TelegramSendResponse:
        return TelegramSendResponse(
            ok=False,
            status_code=500,
            error_code="telegram_http_error",
            error_message=f"failed for {token} and chat {chat_id}",
        )

    with _db(tmp_path) as conn:
        event = _seed_event(conn)

        result = send_alert_event_to_telegram(
            conn,
            event.id,
            env={
                "SAHAMLENS_TELEGRAM_BOT_TOKEN": BOT_SAMPLE_VALUE,
                "SAHAMLENS_TELEGRAM_CHAT_ID": CHAT_SAMPLE_VALUE,
            },
            transport=transport,
        )
        attempts = list_alert_delivery_attempts(conn, event_id=event.id)
        payload = json.dumps([result.model_dump(mode="json"), attempts[0].model_dump(mode="json")])

        assert BOT_SAMPLE_VALUE not in payload
        assert CHAT_SAMPLE_VALUE not in payload


def test_telegram_send_missing_event_is_structured_not_found(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        result = send_alert_event_to_telegram(conn, "missing-event", env={})

        assert result.ok is False
        assert result.status == "not_found"
        assert result.errors[0]["code"] == "not_found"


def test_telegram_message_is_calm_and_not_signal_language(tmp_path: Path) -> None:
    with _db(tmp_path) as conn:
        event = _seed_event(conn)
        message = format_telegram_alert_message(event)

        assert "SahamLens alert event" in message
        assert "Review freshness and confidence" in message
        lowered = message.lower()
        assert "buy signal" not in lowered
        assert "sell signal" not in lowered
        assert "profit opportunity" not in lowered


def _db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "telegram.duckdb"))
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
    return conn


def _seed_event(conn: duckdb.DuckDBPyConnection) -> AlertEvent:
    rule = create_alert_rule(
        conn,
        AlertRuleInput(
            name="BBCA threshold review",
            description="Local threshold review",
            rule_type="price_above",
            ticker="BBCA",
            parameters={"threshold": 9000},
            now=NOW,
        ),
    )
    evaluation = AlertEvaluation(
        id="alert-eval-telegram-test",
        rule_id=rule.id,
        ticker=rule.ticker,
        evaluated_at=NOW,
        status="success",
        reason="Rule condition matched with value 9500 and threshold 9000.",
        data_freshness_status="fresh",
        confidence_status="medium",
        matched=True,
        details={"value": 9500, "threshold": 9000},
    )
    insert_alert_evaluation(conn, evaluation)
    event = AlertEvent(
        id="alert-event-telegram-test",
        rule_id=rule.id,
        evaluation_id=evaluation.id,
        ticker=rule.ticker,
        event_type="price_above",
        severity="info",
        title="Rule condition matched",
        message="BBCA.JK matched price_above. Review freshness and confidence before acting.",
        status="new",
        created_at=NOW,
    )
    return insert_alert_event(conn, event)
