# ADR-0005: Provider-Agnostic LLM Wrapper

Status: Accepted
Date: 2026-05-31

## Context

AI features support explanation, critique, and summarization. The product should not hardcode a model vendor inside feature modules.

## Decision

All LLM calls must go through `packages/core/ai`.

The wrapper owns:

- Provider selection.
- Prompt templates.
- Safety validation.
- Structured output validation.
- Budget/circuit-breaker behavior where implemented.

## Consequences

Positive:

- Feature modules remain provider-ready.
- Safety rules are centralized.
- Testing can mock one boundary.

Trade-offs:

- The wrapper becomes a critical integration point.
- Prompt and schema changes need careful review.

## Follow-Up

Multi-provider UX is not a V1 feature. Provider-ready internals are allowed.
