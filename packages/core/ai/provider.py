"""LLM provider abstraction (ADR-0005, ADR-0021).

Two concrete providers, both using stdlib urllib only (no vendor SDK):
- `AnthropicProvider` — Anthropic Messages API (tool_use for structured output).
- `OpenAICompatibleProvider` — any OpenAI-compatible Chat Completions endpoint
  (DeepSeek, OpenRouter, ...) selected by base_url/api_key/model.

`resolve_provider()` builds the configured provider from the environment.
Providers must NEVER raise through `complete`/`complete_json` — return None on
transient failure so the caller can fall back, log, and proceed. Secrets are read
from the environment only and never rendered.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable, Mapping
from typing import Any, Protocol, runtime_checkable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
OPENAI_COMPAT_COMPLETIONS_PATH = "/chat/completions"
DEFAULT_BACKOFF_S: tuple[float, ...] = (1.0, 2.0, 4.0)
DEFAULT_TIMEOUT_S = 30.0
RETRYABLE_STATUS = (429, 500, 502, 503, 504)

# Environment keys for provider selection. Secrets come only from these.
PROVIDER_ENV = "SAHAMLENS_LLM_PROVIDER"
BASE_URL_ENV = "SAHAMLENS_LLM_BASE_URL"
API_KEY_ENV = "SAHAMLENS_LLM_API_KEY"  # pragma: allowlist secret
MODEL_ENV = "SAHAMLENS_LLM_MODEL"
ANTHROPIC_KEY_ENV = "ANTHROPIC_API_KEY"  # pragma: allowlist secret

_OPENAI_COMPAT_KINDS = frozenset(
    {"openai_compatible", "openai", "deepseek", "openrouter", "custom"}
)


@runtime_checkable
class LLMProvider(Protocol):
    """Structured-output contract: emit a JSON payload matching a schema."""

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


@runtime_checkable
class LLMTextProvider(Protocol):
    """Plain-text completion contract, provider-agnostic."""

    name: str

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> str | None: ...


PostFn = Callable[[str, bytes, dict[str, str], float], bytes]


def _default_post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
    req = Request(url, data=body, headers=headers, method="POST")
    with urlopen(req, timeout=timeout) as resp:
        return bytes(resp.read())


def _post_with_backoff(
    post: PostFn,
    url: str,
    body: bytes,
    headers: dict[str, str],
    *,
    backoff_s: tuple[float, ...],
    timeout_s: float,
    provider_name: str,
) -> bytes | None:
    """Shared retry loop. Retries transient HTTP/network errors, returns None on give-up."""
    attempts = (0.0, *backoff_s)
    last_exc: Exception | None = None
    for delay in attempts:
        if delay:
            time.sleep(delay)
        try:
            return post(url, body, headers, timeout_s)
        except HTTPError as exc:
            last_exc = exc
            if exc.code in RETRYABLE_STATUS:
                continue
            logger.warning("%s http error %s: %s", provider_name, exc.code, exc)
            return None
        except URLError as exc:
            last_exc = exc
            continue
        except Exception as exc:
            logger.warning("%s call failed: %s", provider_name, exc)
            return None
    if last_exc is not None:
        logger.warning("%s call exhausted retries: %s", provider_name, last_exc)
    return None


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
        self._api_key = api_key or os.environ.get(ANTHROPIC_KEY_ENV, "")
        self._backoff_s = backoff_s
        self._timeout_s = timeout_s
        self._post = post or _default_post

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    def _send(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not self._api_key:
            logger.warning("%s API key missing; skipping LLM call", self.name)
            return None
        body = json.dumps(payload).encode("utf-8")
        raw = _post_with_backoff(
            self._post,
            ANTHROPIC_URL,
            body,
            self._headers(),
            backoff_s=self._backoff_s,
            timeout_s=self._timeout_s,
            provider_name=self.name,
        )
        if raw is None:
            return None
        try:
            decoded: dict[str, Any] = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning("%s response not JSON: %s", self.name, exc)
            return None
        return decoded

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> str | None:
        decoded = self._send(
            {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
        )
        return None if decoded is None else _extract_anthropic_text(decoded)

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
        decoded = self._send(
            {
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
        )
        return None if decoded is None else _extract_tool_use(decoded, schema_name)


class OpenAICompatibleProvider:
    """Calls any OpenAI-compatible Chat Completions endpoint via stdlib urllib.

    Structured output uses function calling with a forced tool_choice, mirroring
    the Anthropic tool_use contract. The configured `model` wins over the model
    argument so a single BYO-provider config stays in control.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        name: str = "openai_compatible",
        backoff_s: tuple[float, ...] = DEFAULT_BACKOFF_S,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        post: PostFn | None = None,
    ) -> None:
        self.name = name
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key or ""
        self._backoff_s = backoff_s
        self._timeout_s = timeout_s
        self._post = post or _default_post

    def _url(self) -> str:
        return f"{self._base_url}{OPENAI_COMPAT_COMPLETIONS_PATH}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "content-type": "application/json",
        }

    def _send(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not self._api_key or not self._base_url:
            logger.warning("%s base_url or API key missing; skipping LLM call", self.name)
            return None
        body = json.dumps(payload).encode("utf-8")
        raw = _post_with_backoff(
            self._post,
            self._url(),
            body,
            self._headers(),
            backoff_s=self._backoff_s,
            timeout_s=self._timeout_s,
            provider_name=self.name,
        )
        if raw is None:
            return None
        try:
            decoded: dict[str, Any] = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning("%s response not JSON: %s", self.name, exc)
            return None
        return decoded

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> str | None:
        decoded = self._send(
            {
                "model": self._model or model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
        )
        return None if decoded is None else _extract_openai_text(decoded)

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
        decoded = self._send(
            {
                "model": self._model or model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": schema_name,
                            "description": f"Emit a structured {schema_name} payload.",
                            "parameters": schema,
                        },
                    }
                ],
                "tool_choice": {"type": "function", "function": {"name": schema_name}},
            }
        )
        if decoded is None:
            return None
        return _extract_openai_tool_arguments(decoded, schema_name)


def resolve_provider(
    *,
    env: Mapping[str, str] | None = None,
    post: PostFn | None = None,
) -> LLMProvider:
    """Build the configured provider from the environment (BYO-key, secret-from-env).

    Defaults to Anthropic so existing behavior is unchanged when nothing is set.
    """
    values = env if env is not None else os.environ
    kind = values.get(PROVIDER_ENV, "anthropic").strip().lower() or "anthropic"
    if kind == "anthropic":
        return AnthropicProvider(
            api_key=values.get(ANTHROPIC_KEY_ENV, "").strip() or None,
            post=post,
        )
    if kind in _OPENAI_COMPAT_KINDS:
        return OpenAICompatibleProvider(
            base_url=values.get(BASE_URL_ENV, "").strip(),
            model=values.get(MODEL_ENV, "").strip(),
            api_key=values.get(API_KEY_ENV, "").strip() or None,
            name=kind,
            post=post,
        )
    raise ValueError(f"Unknown {PROVIDER_ENV}: {kind!r}")


def _extract_anthropic_text(response: dict[str, Any]) -> str | None:
    """Concatenate text blocks from an Anthropic Messages response."""
    content = response.get("content")
    if not isinstance(content, list):
        return None
    parts = [
        block["text"]
        for block in content
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    ]
    return "".join(parts) if parts else None


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


def _first_openai_message(response: dict[str, Any]) -> dict[str, Any] | None:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    message = first.get("message") if isinstance(first, dict) else None
    return message if isinstance(message, dict) else None


def _extract_openai_text(response: dict[str, Any]) -> str | None:
    """Return assistant message content from an OpenAI-compatible response."""
    message = _first_openai_message(response)
    if message is None:
        return None
    content = message.get("content")
    return content if isinstance(content, str) and content else None


def _extract_openai_tool_arguments(
    response: dict[str, Any], schema_name: str
) -> dict[str, Any] | None:
    """Parse forced function-call arguments; fall back to message content as JSON."""
    message = _first_openai_message(response)
    if message is None:
        return None
    tool_calls = message.get("tool_calls")
    if isinstance(tool_calls, list):
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            function = call.get("function")
            if not isinstance(function, dict):
                continue
            if function.get("name") != schema_name:
                continue
            parsed = _loads_dict(function.get("arguments"))
            if parsed is not None:
                return parsed
    return _loads_dict(message.get("content"))


def _loads_dict(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, str):
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
