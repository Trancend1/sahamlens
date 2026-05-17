# ADR-0005 — LLM Provider Wrapper (Swap-able)

- **Status:** accepted
- **Date:** 2026-05-16
- **Deciders:** owner

## Context

Sistem butuh LLM untuk news summarization, daily brief, indicator explanation, journal critique, chat. Pilihan vendor: Anthropic Claude (default), OpenAI, Google, local model (Ollama). Cost, kualitas, dan privacy policy vendor bisa berubah.

Pertanyaan: apakah lock ke satu vendor SDK langsung di business logic?

## Decision

**Buat provider wrapper** (`packages/core/ai/provider.py`) sebagai abstraction layer. Business logic depend ke wrapper interface, bukan ke SDK vendor. Default routing: Claude (Haiku/Sonnet/Opus berdasarkan task — lihat [ARCHITECTURE.md §9](../ARCHITECTURE.md)).

Interface minimum:
```python
class LLMProvider(Protocol):
    def complete(
        self,
        template_id: str,
        context: dict,
        schema: type[BaseModel],
        max_tokens: int = 2048,
    ) -> LLMResponse: ...
```

Wrapper handle: prompt template loading, redaction, schema validation, retry, cost tracking, audit log write.

## Consequences

**Positive:**
- Bisa swap provider tanpa ubah business logic.
- Centralized place untuk redaction, audit, cost tracking.
- Unit test business logic dengan mock provider.
- Bisa A/B model untuk task tertentu (V1+).

**Negative:**
- Abstraction overhead — wrapper menutupi beberapa fitur vendor-specific (tool use advanced, vision input).
- Wrapper itu sendiri code yang harus di-maintain.

**Trigger untuk re-evaluate:**
- Wrapper jadi obstacle untuk fitur kritis (e.g. Claude tool use yang kompleks tidak bisa di-abstraksi).
- Owner cuma pakai satu vendor selamanya — abstraction jadi overkill.

## Alternatives Considered

1. **Direct SDK call dari business logic** — di-reject: lock-in, sulit test, redaction & audit jadi scatter.
2. **LangChain / LlamaIndex** — di-reject: framework heavy, abstraksi yang tidak fit (chain-of-thought, memory) untuk RAG-first single-user, dependency churn tinggi.
3. **LiteLLM** — boleh dipertimbangkan kalau provider growth banyak; saat ini wrapper custom 50 LOC lebih ringan.

## Related

- [AI_BOUNDARIES.md §3, §4, §7, §8](../AI_BOUNDARIES.md)
- [SECURITY.md §4](../SECURITY.md)
- [ARCHITECTURE.md §9](../ARCHITECTURE.md)
