"""OpenAICompatibleProvider + resolve_provider: complete/complete_json, env-driven selection."""

from __future__ import annotations

import io
import json
from typing import Any
from urllib.error import HTTPError

import pytest
from packages.core.ai.provider import (
    AnthropicProvider,
    LLMProvider,
    LLMTextProvider,
    OpenAICompatibleProvider,
    resolve_provider,
)

BASE_URL = "https://api.deepseek.com/v1"
SCHEMA = {"type": "object", "properties": {"summary": {"type": "string"}}}
FAKE_API_KEY = "sk-test"  # pragma: allowlist secret


def _text_response(content: str) -> bytes:
    return json.dumps(
        {"choices": [{"message": {"role": "assistant", "content": content}}]}
    ).encode()


def _tool_response(name: str, arguments: dict[str, Any]) -> bytes:
    return json.dumps(
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "type": "function",
                                "function": {"name": name, "arguments": json.dumps(arguments)},
                            }
                        ],
                    }
                }
            ]
        }
    ).encode()


def _provider(
    post: Any, *, model: str = "deepseek-chat", api_key: str = FAKE_API_KEY
) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(base_url=BASE_URL, model=model, api_key=api_key, post=post)


def test_complete_returns_message_content_and_targets_completions_url() -> None:
    seen: dict[str, Any] = {}

    def post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
        seen["url"] = url
        seen["auth"] = headers["Authorization"]
        seen["payload"] = json.loads(body)
        return _text_response("hello from deepseek")

    out = _provider(post).complete(system="s", user="u", model="ignored-by-config")
    assert out == "hello from deepseek"
    assert seen["url"] == "https://api.deepseek.com/v1/chat/completions"
    assert seen["auth"] == f"Bearer {FAKE_API_KEY}"
    # Configured model wins over the caller-supplied model.
    assert seen["payload"]["model"] == "deepseek-chat"


def test_complete_json_extracts_forced_tool_arguments() -> None:
    def post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
        return _tool_response("news_summary", {"summary": "ok."})

    out = _provider(post).complete_json(
        system="s", user="u", schema=SCHEMA, schema_name="news_summary", model="m"
    )
    assert out == {"summary": "ok."}


def test_complete_json_falls_back_to_content_json() -> None:
    def post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
        return _text_response(json.dumps({"summary": "from content"}))

    out = _provider(post).complete_json(
        system="s", user="u", schema=SCHEMA, schema_name="news_summary", model="m"
    )
    assert out == {"summary": "from content"}


def test_returns_none_without_api_key() -> None:
    called = False

    def post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
        nonlocal called
        called = True
        return _text_response("x")

    provider = _provider(post, api_key="")
    assert provider.complete(system="s", user="u", model="m") is None
    assert (
        provider.complete_json(system="s", user="u", schema=SCHEMA, schema_name="n", model="m")
        is None
    )
    assert called is False


def test_returns_none_without_base_url() -> None:
    provider = OpenAICompatibleProvider(base_url="", model="m", api_key=FAKE_API_KEY)
    assert provider.complete(system="s", user="u", model="m") is None


def test_retries_on_429_then_succeeds() -> None:
    attempts: list[int] = []

    def post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
        attempts.append(1)
        if len(attempts) == 1:
            raise HTTPError(url, 429, "rate limited", {}, io.BytesIO(b""))  # type: ignore[arg-type]
        return _text_response("recovered")

    provider = OpenAICompatibleProvider(
        base_url=BASE_URL, model="m", api_key=FAKE_API_KEY, backoff_s=(0.0,), post=post
    )
    assert provider.complete(system="", user="", model="m") == "recovered"
    assert len(attempts) == 2


def test_resolve_defaults_to_anthropic() -> None:
    provider = resolve_provider(env={})
    assert isinstance(provider, AnthropicProvider)
    assert provider.name == "anthropic"


def test_resolve_builds_openai_compatible_from_env() -> None:
    provider = resolve_provider(
        env={
            "SAHAMLENS_LLM_PROVIDER": "deepseek",
            "SAHAMLENS_LLM_BASE_URL": BASE_URL,
            "SAHAMLENS_LLM_API_KEY": FAKE_API_KEY,
            "SAHAMLENS_LLM_MODEL": "deepseek-chat",
        }
    )
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.name == "deepseek"


def test_resolve_tokenrouter() -> None:
    provider = resolve_provider(
        env={
            "SAHAMLENS_LLM_PROVIDER": "tokenrouter",
            "SAHAMLENS_LLM_BASE_URL": "https://api.tokenrouter.io/v1",
            "SAHAMLENS_LLM_API_KEY": FAKE_API_KEY,
            "SAHAMLENS_LLM_MODEL": "MiniMax-M3",
        }
    )
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.name == "tokenrouter"


def test_resolve_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="SAHAMLENS_LLM_PROVIDER"):
        resolve_provider(env={"SAHAMLENS_LLM_PROVIDER": "made-up"})


def test_both_providers_satisfy_text_and_json_protocols() -> None:
    anthropic = AnthropicProvider(api_key=FAKE_API_KEY)
    openai_compat = OpenAICompatibleProvider(base_url=BASE_URL, model="m", api_key=FAKE_API_KEY)
    for provider in (anthropic, openai_compat):
        assert isinstance(provider, LLMProvider)
        assert isinstance(provider, LLMTextProvider)
