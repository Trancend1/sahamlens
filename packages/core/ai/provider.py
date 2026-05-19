"""LLM provider abstraction. Concrete `AnthropicProvider` uses stdlib urllib only.

Provider implementations must NEVER raise through `complete_json` — return None on
transient failure so the caller can fall back, log, and proceed.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_BACKOFF_S: tuple[float, ...] = (1.0, 2.0, 4.0)
DEFAULT_TIMEOUT_S = 30.0


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        schema_name: str,
        model: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> dict[str, Any] | None: ...


PostFn = Callable[[str, bytes, dict[str, str], float], bytes]


def _default_post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
    req = Request(url, data=body, headers=headers, method="POST")
    with urlopen(req, timeout=timeout) as resp:
        return bytes(resp.read())


class AnthropicProvider:
    """Calls Anthropic Messages API via stdlib urllib. No third-party SDK."""

    name = "anthropic"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        backoff_s: tuple[float, ...] = DEFAULT_BACKOFF_S,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        post: PostFn | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._backoff_s = backoff_s
        self._timeout_s = timeout_s
        self._post = post or _default_post

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        schema_name: str,
        model: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> dict[str, Any] | None:
        if not self._api_key:
            logger.warning("ANTHROPIC_API_KEY missing; skipping LLM call")
            return None

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "tools": [
                {
                    "name": schema_name,
                    "description": f"Emit a structured {schema_name} payload.",
                    "input_schema": schema,
                }
            ],
            "tool_choice": {"type": "tool", "name": schema_name},
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        raw = self._post_with_backoff(body, headers)
        if raw is None:
            return None
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning("anthropic response not JSON: %s", exc)
            return None
        return _extract_tool_use(decoded, schema_name)

    def _post_with_backoff(self, body: bytes, headers: dict[str, str]) -> bytes | None:
        attempts = (0.0, *self._backoff_s)
        last_exc: Exception | None = None
        for delay in attempts:
            if delay:
                time.sleep(delay)
            try:
                return self._post(ANTHROPIC_URL, body, headers, self._timeout_s)
            except HTTPError as exc:
                last_exc = exc
                if exc.code in (429, 500, 502, 503, 504):
                    continue
                logger.warning("anthropic http error %s: %s", exc.code, exc)
                return None
            except URLError as exc:
                last_exc = exc
                continue
            except Exception as exc:
                logger.warning("anthropic call failed: %s", exc)
                return None
        if last_exc is not None:
            logger.warning("anthropic call exhausted retries: %s", last_exc)
        return None


def _extract_tool_use(response: dict[str, Any], schema_name: str) -> dict[str, Any] | None:
    """Pull the `input` payload of the first matching `tool_use` content block."""
    content = response.get("content")
    if not isinstance(content, list):
        return None
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "tool_use":
            continue
        if block.get("name") != schema_name:
            continue
        payload = block.get("input")
        if isinstance(payload, dict):
            return payload
    return None
