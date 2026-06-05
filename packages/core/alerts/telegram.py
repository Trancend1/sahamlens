"""Optional Telegram delivery for local alert events."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any, Literal
from urllib import request
from urllib.error import URLError
from uuid import uuid4

import duckdb
from packages.core.alerts.models import AlertDeliveryAttempt, AlertEvent
from packages.core.alerts.repo import (
    get_alert_event,
    insert_alert_delivery_attempt,
)
from pydantic import BaseModel, Field

TELEGRAM_CHANNEL: Literal["telegram"] = "telegram"
TOKEN_ENV = "SAHAMLENS_TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "SAHAMLENS_TELEGRAM_CHAT_ID"

TelegramStatusValue = Literal["configured", "not_configured", "disabled"]
TelegramDeliveryStatusValue = Literal[
    "sent",
    "skipped_not_configured",
    "failed",
    "not_found",
]
TelegramTransport = Callable[[str, str, str], "TelegramSendResponse"]


class TelegramConfigStatus(BaseModel):
    enabled: bool
    configured: bool
    status: TelegramStatusValue
    bot_token_configured: bool
    chat_id_configured: bool
    message: str
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class TelegramSendResponse(BaseModel):
    ok: bool
    status_code: int | None = None
    error_code: str | None = None
    error_message: str | None = None


class TelegramDeliveryResult(BaseModel):
    ok: bool
    status: TelegramDeliveryStatusValue
    event_id: str | None = None
    attempt: AlertDeliveryAttempt | None = None
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    recommended_commands: list[str] = Field(default_factory=list)


def get_telegram_status(
    *,
    env: Mapping[str, str] | None = None,
) -> TelegramConfigStatus:
    values = env if env is not None else os.environ
    token = values.get(TOKEN_ENV, "").strip()
    chat_id = values.get(CHAT_ID_ENV, "").strip()
    token_configured = bool(token)
    chat_configured = bool(chat_id)
    configured = token_configured and chat_configured
    if configured:
        return TelegramConfigStatus(
            enabled=True,
            configured=True,
            status="configured",
            bot_token_configured=True,
            chat_id_configured=True,
            message="Telegram delivery is configured.",
        )
    return TelegramConfigStatus(
        enabled=False,
        configured=False,
        status="not_configured",
        bot_token_configured=token_configured,
        chat_id_configured=chat_configured,
        message="Telegram delivery is optional and not configured.",
        warnings=[
            {
                "code": "telegram_not_configured",
                "message": "Local alert events remain available without Telegram delivery.",
            }
        ],
    )


def send_alert_event_to_telegram(
    conn: duckdb.DuckDBPyConnection,
    event_id: str,
    *,
    env: Mapping[str, str] | None = None,
    transport: TelegramTransport | None = None,
    attempted_at: datetime | None = None,
) -> TelegramDeliveryResult:
    event = get_alert_event(conn, event_id)
    if event is None:
        return TelegramDeliveryResult(
            ok=False,
            status="not_found",
            event_id=event_id,
            errors=[{"code": "not_found", "message": "Alert event was not found."}],
        )

    values = env if env is not None else os.environ
    status = get_telegram_status(env=values)
    now = attempted_at or datetime.now(UTC)
    if not status.configured:
        attempt = _record_attempt(
            conn,
            event,
            status="skipped_not_configured",
            attempted_at=now,
            error_code="telegram_not_configured",
            error_message="Telegram delivery is not configured.",
            redacted_details={
                "bot_token_configured": status.bot_token_configured,
                "chat_id_configured": status.chat_id_configured,
            },
        )
        return TelegramDeliveryResult(
            ok=True,
            status="skipped_not_configured",
            event_id=event.id,
            attempt=attempt,
            warnings=status.warnings,
        )

    token = values[TOKEN_ENV].strip()
    chat_id = values[CHAT_ID_ENV].strip()
    sender = transport or _send_telegram_http
    message = format_telegram_alert_message(event)
    response = sender(token, chat_id, message)
    if response.ok:
        attempt = _record_attempt(
            conn,
            event,
            status="sent",
            attempted_at=now,
            redacted_details={"status_code": response.status_code},
        )
        return TelegramDeliveryResult(ok=True, status="sent", event_id=event.id, attempt=attempt)

    attempt = _record_attempt(
        conn,
        event,
        status="failed",
        attempted_at=now,
        error_code=response.error_code or "telegram_delivery_failed",
        error_message=_safe_error_message(
            response.error_message,
            secrets=[token, chat_id],
        ),
        redacted_details={"status_code": response.status_code},
    )
    return TelegramDeliveryResult(
        ok=False,
        status="failed",
        event_id=event.id,
        attempt=attempt,
        errors=[
            {
                "code": response.error_code or "telegram_delivery_failed",
                "message": _safe_error_message(response.error_message, secrets=[token, chat_id]),
            }
        ],
    )


def format_telegram_alert_message(event: AlertEvent) -> str:
    return "\n".join(
        [
            "SahamLens alert event",
            f"Title: {event.title}",
            f"Ticker: {event.ticker}",
            f"Rule: {event.event_type}",
            f"Severity: {event.severity}",
            f"Status: {event.status}",
            f"Created: {event.created_at.isoformat()}",
            f"Context: {_compact(event.message)}",
            "Review freshness and confidence before making decisions.",
            "This is decision support, not a trading instruction.",
        ]
    )


def _record_attempt(
    conn: duckdb.DuckDBPyConnection,
    event: AlertEvent,
    *,
    status: Literal["skipped_not_configured", "sent", "failed"],
    attempted_at: datetime,
    error_code: str | None = None,
    error_message: str | None = None,
    redacted_details: dict[str, Any] | None = None,
) -> AlertDeliveryAttempt:
    attempt = AlertDeliveryAttempt(
        id=f"alert-delivery-{uuid4().hex}",
        event_id=event.id,
        channel=TELEGRAM_CHANNEL,
        status=status,
        attempted_at=attempted_at,
        error_code=error_code,
        error_message=_safe_error_message(error_message),
        redacted_details=redacted_details or {},
    )
    return insert_alert_delivery_attempt(conn, attempt)


def _send_telegram_http(token: str, chat_id: str, text: str) -> TelegramSendResponse:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
    ).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            status_code = int(response.status)
            return TelegramSendResponse(ok=200 <= status_code < 300, status_code=status_code)
    except URLError as exc:
        return TelegramSendResponse(
            ok=False,
            error_code="telegram_network_error",
            error_message=_safe_error_message(str(exc), secrets=[token, chat_id]),
        )


def _compact(value: str, *, limit: int = 220) -> str:
    compact = " ".join(value.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 3]}..."


def _safe_error_message(
    value: str | None,
    *,
    secrets: list[str] | None = None,
) -> str | None:
    if not value:
        return None
    redacted = value.replace(TOKEN_ENV, "TELEGRAM_TOKEN")
    for secret in secrets or []:
        if secret:
            redacted = redacted.replace(secret, "[redacted]")
    return redacted[:240]
