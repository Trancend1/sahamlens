"""LLM provider configuration status check.

Read-only introspection of the configured LLM provider — no API calls made.
Returns JSON with provider name, whether it's configured, and model info.
Used by WebUI to show configuration status without making costly API calls.
"""

from __future__ import annotations

import json
import sys

from dotenv import load_dotenv

load_dotenv(".env.local")

from packages.core.ai.provider import (  # noqa: E402
    AnthropicProvider,
    OpenAICompatibleProvider,
    resolve_provider,
)


def check_status() -> dict[str, object]:
    """Inspect provider config without making any API call."""
    try:
        provider = resolve_provider()
    except ValueError as exc:
        return {
            "configured": False,
            "provider": "unknown",
            "model": "",
            "error": str(exc),
        }

    result: dict[str, object] = {
        "configured": False,
        "provider": provider.name,
        "model": "",
        "error": None,
    }

    if isinstance(provider, AnthropicProvider):
        key_ok = bool(provider._api_key)
        result["configured"] = key_ok
        result["model"] = "claude (Anthropic)"
        if not key_ok:
            result["error"] = "ANTHROPIC_API_KEY not set"

    elif isinstance(provider, OpenAICompatibleProvider):
        key_ok = bool(provider._api_key)
        url_ok = bool(provider._base_url)
        result["configured"] = key_ok and url_ok
        result["model"] = provider._model or "(default)"
        if not key_ok and not url_ok:
            result["error"] = "SAHAMLENS_LLM_API_KEY and SAHAMLENS_LLM_BASE_URL not set"
        elif not key_ok:
            result["error"] = "SAHAMLENS_LLM_API_KEY not set"
        elif not url_ok:
            result["error"] = "SAHAMLENS_LLM_BASE_URL not set"

    else:
        result["error"] = f"Unknown provider type: {type(provider).__name__}"

    return result


def main() -> int:
    status = check_status()
    json.dump(status, sys.stdout, indent=2)
    return 0 if status["configured"] else 1


if __name__ == "__main__":
    sys.exit(main())
