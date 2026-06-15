"""Tests for Telegram listener: update handling, confirmation flow, transport."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
from packages.core.ai.provider import AnthropicProvider
from packages.core.ai.router import CircuitBreaker, CostBudget, ModelRouter
from packages.core.alerts.telegram import TelegramSendResponse
from scripts.migrate import applied_versions, apply_migration, discover_migrations

from services.hermes.telegram_listener import (
    TelegramListener,
    _is_confirmation,
)


def _migrated_db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
    return conn


def _fake_provider() -> AnthropicProvider:
    def fake_post(*args: Any, **kwargs: Any) -> bytes:
        return json.dumps(
            {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "stock_brief",
                        "input": {
                            "evidence": [
                                {
                                    "type": "price",
                                    "value": "Stable",
                                    "source_ref": "test",
                                    "freshness": "2026-06-15",
                                }
                            ],
                            "bullish_view": "OK",
                            "bearish_view": "Risk",
                            "uncertainty": "Earnings",
                            "caveats": ["DYOR"],
                            "beginner_explanation": "Simple",
                            "suggested_next_question": "Check",
                        },
                    }
                ],
            }
        ).encode("utf-8")

    return AnthropicProvider(api_key="sk-test", post=fake_post)  # pragma: allowlist secret


def _make_update(text: str, update_id: int = 1) -> dict[str, Any]:
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id,
            "date": int(datetime.now(UTC).timestamp()),
            "text": text,
            "chat": {"id": 12345, "type": "private"},
            "from": {"id": 999, "is_bot": False, "first_name": "Test"},
        },
    }


def _noop_send(token: str, chat_id: str, text: str) -> TelegramSendResponse:
    return TelegramSendResponse(ok=True)


def _noop_get_updates(token: str, offset: int | None) -> list[dict[str, Any]]:
    return []


def test_is_confirmation_true() -> None:
    assert _is_confirmation("yes") is True
    assert _is_confirmation("YA") is True
    assert _is_confirmation("Konfirmasi") is True
    assert _is_confirmation("setuju") is True
    assert _is_confirmation("ok") is True


def test_is_confirmation_false() -> None:
    assert _is_confirmation("no") is False
    assert _is_confirmation("/brief BBRI") is False
    assert _is_confirmation("") is False
    assert _is_confirmation("maybe") is False


def test_listener_start_stop(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    try:
        listener = TelegramListener(
            conn=conn,
            provider=None,
            router=ModelRouter(),
            breaker=CircuitBreaker(CostBudget(daily_usd_cap=999.0)),
            session_id="test-sess",
            telegram_token="",
            telegram_chat_id="",
            get_updates_fn=_noop_get_updates,
            send_message_fn=_noop_send,
        )
        assert listener._running is False
        listener.stop()
        assert listener._running is False
    finally:
        conn.close()


def test_listener_handles_help(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    sent_messages: list[str] = []

    def capture_send(token: str, chat_id: str, text: str) -> TelegramSendResponse:
        sent_messages.append(text)
        return TelegramSendResponse(ok=True)

    updates = [_make_update("/help", 1), _make_update("/help", 2)]

    def staged_updates(token: str, offset: int | None) -> list[dict[str, Any]]:
        if offset is None or offset <= 1:
            return [updates[0]]
        if offset <= 2:
            return [updates[1]]
        return []

    try:
        listener = TelegramListener(
            conn=conn,
            provider=None,
            router=ModelRouter(),
            breaker=CircuitBreaker(CostBudget(daily_usd_cap=999.0)),
            session_id="test-sess",
            telegram_token="test:token",
            telegram_chat_id="12345",
            get_updates_fn=staged_updates,
            send_message_fn=capture_send,
        )
        listener._handle_update(_make_update("/help", 1))
        listener._handle_update(_make_update("/help", 2))
        listener.stop()
    finally:
        conn.close()

    assert len(sent_messages) >= 1
    assert any("SahamLens Hermes" in m for m in sent_messages)


def test_listener_handles_unknown(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    sent_messages: list[str] = []

    def capture_send(token: str, chat_id: str, text: str) -> TelegramSendResponse:
        sent_messages.append(text)
        return TelegramSendResponse(ok=True)

    try:
        listener = TelegramListener(
            conn=conn,
            provider=None,
            router=ModelRouter(),
            breaker=CircuitBreaker(CostBudget(daily_usd_cap=999.0)),
            session_id="test-sess",
            telegram_token="test:token",
            telegram_chat_id="12345",
            get_updates_fn=_noop_get_updates,
            send_message_fn=capture_send,
        )
        listener._handle_update(_make_update("gibberish", 1))
        listener.stop()
    finally:
        conn.close()

    assert len(sent_messages) >= 1
    assert any("tidak mengerti" in m for m in sent_messages)


def test_listener_handles_exposure(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    sent_messages: list[str] = []

    def capture_send(token: str, chat_id: str, text: str) -> TelegramSendResponse:
        sent_messages.append(text)
        return TelegramSendResponse(ok=True)

    try:
        listener = TelegramListener(
            conn=conn,
            provider=None,
            router=ModelRouter(),
            breaker=CircuitBreaker(CostBudget(daily_usd_cap=999.0)),
            session_id="test-sess",
            telegram_token="test:token",
            telegram_chat_id="12345",
            get_updates_fn=_noop_get_updates,
            send_message_fn=capture_send,
        )
        listener._handle_update(_make_update("/exposure", 1))
        listener.stop()
    finally:
        conn.close()

    assert len(sent_messages) >= 1
    assert any("portfolio exposure" in m.lower() for m in sent_messages)


def test_listener_confirmation_flow(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    now = datetime.now(UTC)
    sent_messages: list[str] = []

    def capture_send(token: str, chat_id: str, text: str) -> TelegramSendResponse:
        sent_messages.append(text)
        return TelegramSendResponse(ok=True)

    # Set up an alert event
    conn.execute(
        "INSERT INTO alert_rules (id, name, description, rule_type, ticker, "
        "parameters_json, is_active, created_at, updated_at) "
        "VALUES ('rule-c1', 'Test', 'test', 'price_above', 'BBRI', "
        "'{}', 1, ?, ?)",
        [now.isoformat(), now.isoformat()],
    )
    conn.execute(
        "INSERT INTO alert_evaluations (id, rule_id, evaluated_at, status, "
        "reason, data_freshness_status, confidence_status, matched, details_json) "
        "VALUES ('eval-c1', 'rule-c1', ?, 'success', 'test', "
        "'fresh', 'high', 1, '{}')",
        [now.isoformat()],
    )
    conn.execute(
        "INSERT INTO alert_events (id, rule_id, evaluation_id, ticker, "
        "event_type, severity, title, message, status, created_at) "
        "VALUES ('alert-c1', 'rule-c1', 'eval-c1', 'BBRI', "
        "'price_above', 'info', 'Test', 'Test msg', 'new', ?)",
        [now.isoformat()],
    )

    try:
        listener = TelegramListener(
            conn=conn,
            provider=None,
            router=ModelRouter(),
            breaker=CircuitBreaker(CostBudget(daily_usd_cap=999.0)),
            session_id="test-sess",
            telegram_token="test:token",
            telegram_chat_id="12345",
            get_updates_fn=_noop_get_updates,
            send_message_fn=capture_send,
        )
        # First request a write action
        listener._handle_update(_make_update("/alert ack alert-c1", 1))
        # Verify we got a confirmation prompt
        assert any("konfirmasi" in m.lower() for m in sent_messages)

        # Then confirm
        listener._handle_update(_make_update("yes", 2))
        assert any("berhasil" in m.lower() or "applied" in m.lower() for m in sent_messages)

        # Verify the alert was acknowledged
        row = conn.execute("SELECT status FROM alert_events WHERE id = 'alert-c1'").fetchone()
        assert row is not None
        assert row[0] == "acknowledged"
    finally:
        conn.close()


def test_listener_confirmation_without_pending(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    sent_messages: list[str] = []

    def capture_send(token: str, chat_id: str, text: str) -> TelegramSendResponse:
        sent_messages.append(text)
        return TelegramSendResponse(ok=True)

    try:
        listener = TelegramListener(
            conn=conn,
            provider=None,
            router=ModelRouter(),
            breaker=CircuitBreaker(CostBudget(daily_usd_cap=999.0)),
            session_id="test-sess",
            telegram_token="test:token",
            telegram_chat_id="12345",
            get_updates_fn=_noop_get_updates,
            send_message_fn=capture_send,
        )
        listener._handle_update(_make_update("yes", 1))
        listener.stop()
    finally:
        conn.close()

    assert len(sent_messages) >= 1
    assert any("tidak ada aksi" in m.lower() for m in sent_messages)


def test_listener_handles_brief_with_provider(tmp_path: Path) -> None:
    conn = _migrated_db(tmp_path)
    sent_messages: list[str] = []

    def capture_send(token: str, chat_id: str, text: str) -> TelegramSendResponse:
        sent_messages.append(text)
        return TelegramSendResponse(ok=True)

    try:
        listener = TelegramListener(
            conn=conn,
            provider=_fake_provider(),
            router=ModelRouter(),
            breaker=CircuitBreaker(CostBudget(daily_usd_cap=999.0)),
            session_id="test-sess",
            telegram_token="test:token",
            telegram_chat_id="12345",
            get_updates_fn=_noop_get_updates,
            send_message_fn=capture_send,
        )
        listener._handle_update(_make_update("/brief BBRI", 1))
        listener.stop()
    finally:
        conn.close()

    assert len(sent_messages) >= 1
    assert any("SahamLens brief" in m for m in sent_messages)
