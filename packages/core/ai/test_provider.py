"""AnthropicProvider: header building, retry on 429, tool_use extraction, None paths."""

from __future__ import annotations

import io
import json
from urllib.error import HTTPError

from packages.core.ai.provider import AnthropicProvider, _extract_tool_use


def _ok_response(input_payload: dict[str, object]) -> bytes:
    return json.dumps(
        {
            "content": [
                {"type": "tool_use", "name": "news_summary", "input": input_payload},
            ]
        }
    ).encode("utf-8")


def test_complete_json_returns_payload_when_post_ok() -> None:
    calls: list[dict[str, str]] = []

    def fake_post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
        calls.append({"url": url, "x-api-key": headers["x-api-key"]})
        return _ok_response({"summary": "ok.", "sentiment_label": "neutral", "confidence": 0.9})

    provider = AnthropicProvider(api_key="sk-test", post=fake_post)
    out = provider.complete_json(
        system="sys",
        user="usr",
        schema={"type": "object"},
        schema_name="news_summary",
        model="claude-haiku-4-5-20251001",
    )
    assert out is not None
    assert out["summary"] == "ok."
    assert calls[0]["x-api-key"] == "sk-test"


def test_complete_json_returns_none_without_api_key() -> None:
    provider = AnthropicProvider(api_key="")
    out = provider.complete_json(
        system="s",
        user="u",
        schema={"type": "object"},
        schema_name="news_summary",
        model="claude-haiku-4-5-20251001",
    )
    assert out is None


def test_complete_json_retries_on_429_then_succeeds() -> None:
    attempts: list[int] = []

    def fake_post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
        attempts.append(1)
        if len(attempts) == 1:
            raise HTTPError(url, 429, "rate limited", {}, io.BytesIO(b""))  # type: ignore[arg-type]
        return _ok_response({"summary": "x.", "sentiment_label": "neutral", "confidence": 0.9})

    provider = AnthropicProvider(api_key="sk", backoff_s=(0.0,), post=fake_post)
    out = provider.complete_json(
        system="",
        user="",
        schema={"type": "object"},
        schema_name="news_summary",
        model="m",
    )
    assert out is not None
    assert len(attempts) == 2


def test_complete_json_returns_none_on_permanent_4xx() -> None:
    def fake_post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
        raise HTTPError(url, 400, "bad request", {}, io.BytesIO(b""))  # type: ignore[arg-type]

    provider = AnthropicProvider(api_key="sk", post=fake_post)
    out = provider.complete_json(
        system="",
        user="",
        schema={"type": "object"},
        schema_name="news_summary",
        model="m",
    )
    assert out is None


def test_extract_tool_use_returns_none_on_missing_name() -> None:
    response = {"content": [{"type": "tool_use", "name": "other", "input": {}}]}
    assert _extract_tool_use(response, "news_summary") is None


def test_extract_tool_use_returns_none_on_empty_content() -> None:
    assert _extract_tool_use({"content": []}, "news_summary") is None
