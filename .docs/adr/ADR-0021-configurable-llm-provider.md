# ADR-0021: Configurable LLM Provider

Status: Accepted
Date: 2026-06-15
Builds on: ADR-0005 (LLM wrapper), ADR-0019 (agentic runtime), ADR-0020 (env-driven config harvest).
Reference: `.insight/Multi-Provider-Configurability.md`.

Prerequisite for M4. The Hermes runtime must construct its LLM provider from
configuration, not hardcode Anthropic.

## Context

`packages/core/ai` already defines a provider-agnostic `LLMProvider` Protocol
(ADR-0005), but the only concrete implementation was `AnthropicProvider`, and
every entry point (`scripts/*`) constructed it directly. The owner wants to use
other providers — DeepSeek, OpenRouter, and similar — by supplying base URL, API
key, and model, without locking to Anthropic.

This realizes the existing agnostic principle; it does not change product scope or
the local-first / single-user / non-advisory identity.

## Decision

1. **Two Protocols.** Keep `LLMProvider` (structured: `complete_json`) unchanged so
   existing fakes and call sites stay valid. Add `LLMTextProvider`
   (`complete` → plain text). Both concrete providers implement both.

2. **`OpenAICompatibleProvider`.** A new provider speaking the OpenAI-compatible
   Chat Completions API, covering DeepSeek, OpenRouter, and others via configurable
   `base_url` / `api_key` / `model`. Structured output uses function calling with a
   forced `tool_choice`, mirroring the Anthropic `tool_use` contract, with a
   fallback to parsing message content as JSON. The configured `model` wins over
   the caller-supplied model so one BYO-provider config stays in control.

3. **Stdlib only.** No vendor SDK. Both providers use `urllib`, sharing one
   `_post_with_backoff` retry helper. This honors the stack ban on heavy/paid
   dependencies.

4. **Env-driven factory.** `resolve_provider(env=...)` selects the provider:
   `SAHAMLENS_LLM_PROVIDER` (`anthropic` default, or `openai_compatible` /
   `deepseek` / `openrouter` / `openai` / `custom`), with
   `SAHAMLENS_LLM_BASE_URL` / `SAHAMLENS_LLM_API_KEY` / `SAHAMLENS_LLM_MODEL`, and
   `ANTHROPIC_API_KEY` for the Anthropic path. Defaulting to Anthropic keeps
   existing behavior unchanged when nothing is configured.

5. **All entry points use the factory.** `scripts/agent_brief.py`,
   `generate_brief.py`, `journal.py`, and `summarize_news.py` call
   `resolve_provider()` instead of `AnthropicProvider()`.

6. **Safety is provider-agnostic.** `validator.py` (banned-phrase / AI_BOUNDARIES)
   runs after every provider call regardless of provider. Provider choice never
   weakens output safety.

## Constraints Preserved

- **BYO-key.** No provider requires a paid key by default. With no key, calls
  return `None` (no LLM call), exactly like today — no crash, no new mandatory
  dependency.
- **Secret-from-env only.** API keys are read from the environment / `.env.local`,
  never hardcoded, committed, or rendered.
- **Never raise.** Providers return `None` on transient failure so callers fall
  back and log.

## Consequences

Positive:

- Owner can run any OpenAI-compatible provider by setting four env vars.
- Existing Anthropic path and tests are untouched in behavior.
- M4 can construct its provider from config with no further provider work.

Trade-offs / deferred:

- `ModelRouter` still maps task → model with Anthropic-oriented ids; for a custom
  provider the configured model overrides it. Per-provider cost/budget entries and
  per-task provider overrides are deferred to when needed.
- Providers lacking function-calling rely on the JSON-content fallback; strict
  `response_format: json_schema` support is not implemented yet.

## Non-Goals

- Vendor SDKs, streaming, or multi-provider routing per request.
- Changing the AI response contract or validator behavior.
- Any platform/distributed concern (that is ADR-0020's horizon).
