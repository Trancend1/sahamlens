"""Telegram long-polling listener for Hermes runtime (M4.6).

Single-process, offset-tracked, graceful-stop. Uses a fake transport
in tests (no real network).
"""

from __future__ import annotations

import json
import logging
import signal
import time
from collections.abc import Callable, Mapping
from typing import Any, cast
from urllib import request
from urllib.error import URLError

import duckdb
from packages.core.ai.provider import LLMProvider
from packages.core.ai.router import CircuitBreaker, ModelRouter
from packages.core.alerts.telegram import TelegramSendResponse, _send_telegram_http

from services.hermes.dispatch import dispatch_intent
from services.hermes.intents import parse_intent
from services.hermes.policy import check_intent_allowed, check_outbound_text
from services.hermes.writes import confirm_and_apply, request_write_action

logger = logging.getLogger(__name__)

POLL_INTERVAL_S = 2.0
GETUPDATES_TIMEOUT_S = 30
CONFIRMATION_KEYWORDS = frozenset(
    {
        "yes",
        "ya",
        "y",
        "confirm",
        "konfirmasi",
        "setuju",
        "lanjut",
        "ok",
        "oke",
    }
)

_ALERT_ACTION_MAP: dict[str, str] = {
    "ack": "acknowledge_alert",
    "fp": "mark_false_positive",
}

TelegramTransport = Callable[[str, str, str], TelegramSendResponse]
GetUpdatesFn = Callable[[str, int | None], list[dict[str, Any]]]


class TelegramListener:
    """Long-polling Telegram listener. Start/stop lifecycle."""

    def __init__(
        self,
        *,
        conn: duckdb.DuckDBPyConnection,
        provider: LLMProvider | None,
        router: ModelRouter,
        breaker: CircuitBreaker,
        session_id: str,
        telegram_token: str = "",
        telegram_chat_id: str = "",
        env: Mapping[str, str] | None = None,
        get_updates_fn: GetUpdatesFn | None = None,
        send_message_fn: TelegramTransport | None = None,
    ) -> None:
        self._conn = conn
        self._provider = provider
        self._router = router
        self._breaker = breaker
        self._session_id = session_id
        self._telegram_token = telegram_token
        self._telegram_chat_id = telegram_chat_id
        self._env = env
        self._get_updates_fn = get_updates_fn or self._http_get_updates
        self._send_message_fn = send_message_fn
        self._offset: int = 0
        self._running = False

    def start(self) -> None:
        """Enter the polling loop. Blocks until stop() is called or signal received."""
        self._running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Hermes listener started (session %s...)", self._session_id[:8])
        while self._running:
            try:
                updates = self._get_updates_fn(self._telegram_token, self._offset)
                for update in updates:
                    self._handle_update(update)
                    self._offset = max(self._offset, (update.get("update_id") or 0) + 1)
            except Exception as exc:
                logger.warning("Polling error: %s", exc)
            time.sleep(POLL_INTERVAL_S)

    def stop(self) -> None:
        """Signal the polling loop to exit on the next iteration."""
        self._running = False
        logger.info("Hermes listener stopping...")

    def _signal_handler(self, signum: int, _frame: object) -> None:
        logger.info("Received signal %d, stopping...", signum)
        self.stop()

    def _handle_update(self, update: dict[str, Any]) -> None:
        message = update.get("message")
        if not isinstance(message, dict):
            return
        text = message.get("text")
        if not isinstance(text, str) or not text.strip():
            return
        chat_id = message.get("chat", {}).get("id")
        if chat_id is not None:
            self._telegram_chat_id = str(chat_id)

        text = text.strip()

        if _is_confirmation(text):
            self._handle_confirmation(text)
            return

        parsed = parse_intent(text)

        policy = check_intent_allowed(parsed.intent)
        if not policy.allowed:
            self._send(policy.reason)
            return

        result = dispatch_intent(
            parsed,
            conn=self._conn,
            provider=self._provider,
            router=self._router,
            breaker=self._breaker,
            session_id=self._session_id,
            surface="telegram",
        )

        if result.requires_confirmation and result.agent_log_id:
            raw_action = parsed.alert_action or ""
            write_action = _ALERT_ACTION_MAP.get(raw_action, raw_action)
            if not write_action:
                write_action = "alert_triage"
            write_req = request_write_action(
                self._conn,
                agent_log_id=result.agent_log_id,
                action=write_action,
                target_ref=parsed.alert_event_id,
            )
            self._send(write_req.message)
            return

        outbound = check_outbound_text(result.response_text)
        if not outbound.allowed:
            logger.warning("Outbound blocked by policy: %s", outbound.banned_hit)
            self._send(
                "Maaf, respons tidak dapat dikirim karena mengandung "
                "frasa yang tidak diizinkan oleh kebijakan keamanan."
            )
            return

        self._send(result.response_text)

    def _handle_confirmation(self, text: str) -> None:
        row = self._conn.execute(
            """
            SELECT w.idempotency_key, w.action, w.target_ref
            FROM agent_write_action w
            WHERE w.status = 'pending_confirmation'
            ORDER BY w.created_at DESC
            LIMIT 1
            """,
        ).fetchone()

        if row is None:
            self._send(
                "Tidak ada aksi yang menunggu konfirmasi. "
                "Gunakan perintah yang sesuai terlebih dahulu."
            )
            return

        idempotency_key, _action, _target_ref = row
        result = confirm_and_apply(
            self._conn,
            idempotency_key=idempotency_key,
        )
        self._send(result.message)

    def _send(self, text: str) -> None:
        if not self._telegram_token or not self._telegram_chat_id:
            logger.info("[no-telegram] %s", text[:100])
            return
        transport = self._send_message_fn or _send_telegram_http
        transport(self._telegram_token, self._telegram_chat_id, text)

    def _http_get_updates(self, token: str, offset: int | None) -> list[dict[str, Any]]:
        if not token:
            return []
        url = f"https://api.telegram.org/bot{token}/getUpdates?timeout={GETUPDATES_TIMEOUT_S}"
        if offset:
            url += f"&offset={offset}"
        try:
            with request.urlopen(url, timeout=GETUPDATES_TIMEOUT_S + 5) as resp:
                data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        except (URLError, json.JSONDecodeError, OSError) as exc:
            logger.warning("getUpdates failed: %s", exc)
            return []
        if not data.get("ok"):
            return []
        return cast("list[dict[str, Any]]", data.get("result", []))


def _is_confirmation(text: str) -> bool:
    return text.strip().lower() in CONFIRMATION_KEYWORDS
