"""Hermes runtime configuration — env-driven, secret-safe (ADR-0021, M4.1).

Reads environment variables to determine runtime state. Never renders secrets.
Default: disabled. User must explicitly opt in via SAHAMLENS_HERMES_ENABLED=1.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Mapping

from packages.core.ai.provider import LLMProvider, resolve_provider
from pydantic import BaseModel

ENABLED_ENV = "SAHAMLENS_HERMES_ENABLED"
TELEGRAM_TOKEN_ENV = "SAHAMLENS_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID_ENV = "SAHAMLENS_TELEGRAM_CHAT_ID"
PROVIDER_ENV = "SAHAMLENS_LLM_PROVIDER"
ANTHROPIC_KEY_ENV = "ANTHROPIC_API_KEY"
API_KEY_ENV = "SAHAMLENS_LLM_API_KEY"  # pragma: allowlist secret


class HermesConfig(BaseModel):
    """Immutable runtime config snapshot. Never holds raw secrets.

    Use `load_config()` to build from environment. Check `enabled` first
    before starting the listener — a disabled config is not an error.
    """

    enabled: bool = False
    session_id: str = ""
    telegram_token_configured: bool = False
    telegram_chat_id_configured: bool = False
    telegram_configured: bool = False
    provider_name: str = ""
    provider_configured: bool = False

    def status_text(self) -> str:
        if not self.enabled:
            return "Hermes runtime disabled (set SAHAMLENS_HERMES_ENABLED=1)."
        parts = [
            f"Hermes session {self.session_id[:12]}...",
            f"Telegram: {'configured' if self.telegram_configured else 'not configured'}",
            f"LLM: {self.provider_name} ({'configured' if self.provider_configured else 'missing key'})",
        ]
        return " | ".join(parts)


def load_config(
    *,
    env: Mapping[str, str] | None = None,
) -> tuple[HermesConfig, LLMProvider | None]:
    """Read environment and build config + resolved provider.

    Returns (config, provider). Provider is None when Hermes is disabled.
    Never raises for missing env vars — returns a disabled config instead.
    """
    values = env if env is not None else os.environ

    enabled = values.get(ENABLED_ENV, "").strip() in ("1", "true", "yes")
    session_id = uuid.uuid4().hex if enabled else ""

    telegram_token = bool(values.get(TELEGRAM_TOKEN_ENV, "").strip())
    telegram_chat = bool(values.get(TELEGRAM_CHAT_ID_ENV, "").strip())

    provider_name = values.get(PROVIDER_ENV, "anthropic").strip().lower() or "anthropic"

    provider: LLMProvider | None = None
    provider_configured = False

    if enabled:
        try:
            provider = resolve_provider(env=values)
        except ValueError:
            provider = None

        if provider is not None:
            if provider_name == "anthropic":
                provider_configured = bool(values.get(ANTHROPIC_KEY_ENV, "").strip())
            else:
                provider_configured = bool(values.get(API_KEY_ENV, "").strip())

    config = HermesConfig(
        enabled=enabled,
        session_id=session_id,
        telegram_token_configured=telegram_token,
        telegram_chat_id_configured=telegram_chat,
        telegram_configured=telegram_token and telegram_chat,
        provider_name=provider_name,
        provider_configured=provider_configured,
    )
    return config, provider if enabled else None
