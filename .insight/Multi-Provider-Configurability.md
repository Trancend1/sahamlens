# Insight: Multi-Provider LLM Configurability

## Context

The owner wants the LLM provider to not be locked to the Anthropic API. It should
be customizable so the owner can use providers such as DeepSeek, OpenRouter, or
others by supplying a base URL, API key, model name, and related settings as
needed.

## Alignment (not a conflict)

This realizes an already-locked principle, it does not contradict it:

- Stack: "AI — provider-agnostic wrapper in `packages/core/ai`" (ADR-0005).
- `packages/core/ai/provider.py` already defines an `LLMProvider` Protocol; only
  the concrete `AnthropicProvider` and the CLI wiring (`AnthropicProvider()` in
  `scripts/agent_brief.py`, `scripts/generate_brief.py`) are Anthropic-specific.
- Core call sites (`generate_stock_brief`, `answer_stock_question`) accept
  `provider: LLMProvider`, so swapping the provider is a wiring + config change,
  not a rewrite.

## Technical Shape

- Most non-Anthropic targets (DeepSeek, OpenRouter, and many others) speak the
  OpenAI-compatible Chat Completions API. A single `OpenAICompatibleProvider`
  (stdlib urllib, no new SDK dependency) can cover many of them via configurable
  `base_url` / `api_key` / `model`.
- Key design consideration: structured JSON output differs by API. Anthropic uses
  `tool_use` + `input_schema`; OpenAI-compatible uses function/tool calling,
  `response_format: json_schema`, or JSON mode. The `complete_json` contract
  (return a dict matching the schema, never raise, return None on transient
  failure) must be honored per provider. `packages/core/ai/validator.py` stays the
  safety net regardless of provider.
- Config should be env-driven (consistent with ADR-0019 and the ADR-0020 harvest),
  e.g. `SAHAMLENS_LLM_PROVIDER`, `SAHAMLENS_LLM_BASE_URL`, `SAHAMLENS_LLM_API_KEY`,
  `SAHAMLENS_LLM_MODEL`. Provider selection resolves to the right `LLMProvider`.

## Constraints to Preserve

- BYO key only: no provider may require a paid API key by default (stack ban). The
  owner supplies the key; default with no key = no LLM call (same as today).
- Safety unchanged: banned-phrase / AI_BOUNDARIES validation runs after every
  provider call, no matter the provider.
- Public-repo-safe: API keys come from env / `.env.local`, never committed or
  rendered.
- No heavy dependency: keep the stdlib-urllib approach; do not pull in vendor SDKs.

## Open Questions (for the implementation ADR / M4)

- Which structured-output mode per provider (function calling vs json_schema vs
  JSON mode), and graceful fallback when a model lacks tool support.
- Per-provider cost/budget config: `CircuitBreaker` budget is model-keyed today;
  may need per-provider cost entries.
- Model routing: `ModelRouter` currently maps task -> model; how it interacts with
  a configurable provider/model pair.
- Optional per-task provider override vs a single global provider.

## Recommendation

Fold provider configurability into M4 as a prerequisite (the runtime should read
provider config from env and construct the right `LLMProvider`), and capture the
decision in a thin ADR-0021 (Configurable LLM Provider). No implementation yet;
this is an insight to inform M4 scope.
