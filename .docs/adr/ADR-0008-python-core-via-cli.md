# ADR-0008 — Python Core Diekspos via CLI, Bukan Separate HTTP Service

- **Status:** accepted
- **Date:** 2026-05-16
- **Deciders:** owner

## Context

Stack pakai dua bahasa: Python (data core, financial calc, AI orchestration) dan TypeScript (Next.js UI). Ada dua cara menghubungkan:

1. **Separate HTTP service** — Python FastAPI listening di port lokal, Next.js fetch via HTTP.
2. **CLI invocation** — Next.js spawn Python process via child_process untuk heavy ops; light reads via DuckDB direct query.

Pertanyaan: pilih yang mana?

## Decision

**CLI invocation untuk heavy ops + DuckDB direct read untuk light query**, **tidak ada** separate HTTP server di MVP.

Konkret:
- **Read OHLCV, watchlist, journal:** Next.js (Server Component / API route) langsung query DuckDB lokal via `duckdb` Node binding atau via `node-duckdb`.
- **Heavy ops (indicator batch recalc, AI generation, news ingestion):** Next.js API route spawn Python script (`scripts/*.py`). Output structured JSON via stdout, error via exit code + stderr.
- **Cron-driven ingestion:** OS cron langsung memanggil `scripts/*.py`. Tidak butuh Next.js sama sekali.

## Consequences

**Positive:**
- Satu boundary lebih sedikit (tidak ada server Python yang harus jalan).
- Tidak ada port conflict / health check loop.
- Cold start acceptable untuk personal use (1–3 detik).
- Cron lokal natural — `python scripts/foo.py`, tanpa HTTP.
- Deploy lebih sederhana (kalau pun hosted).

**Negative:**
- Tidak cocok kalau request rate tinggi (acceptable: single user).
- Spawn overhead per call (~200ms warm cache).
- Lebih sulit streaming response (kalau butuh streaming AI chat, lihat re-evaluate).

**Trigger untuk re-evaluate (= switch ke FastAPI):**
- Request latency dari spawn jadi UX problem.
- Butuh streaming response (Server-Sent Events untuk AI chat).
- Hosted dashboard multi-tenant (tidak akan, lihat scope).

Note: streaming chat AI bisa di-handle dengan Next.js API route langsung memanggil Anthropic SDK (TypeScript), bypass Python untuk path tersebut. Provider wrapper di-implement dual (TS + Python) untuk shared LLM call kalau diperlukan. Lihat [ADR-0005](ADR-0005-llm-wrapper.md).

## Alternatives Considered

1. **FastAPI dari awal** — di-reject MVP: dua server untuk single user adalah operational theater. Re-evaluate di V1 kalau butuh streaming.
2. **Rewrite data core di TypeScript** — di-reject: ekosistem data science (pandas, pandas-ta) jauh lebih kuat di Python.
3. **WebAssembly Python (Pyodide)** — di-reject: bundle size besar, ekosistem terbatas, tidak fit untuk cron-driven ingestion.

## Implementation Notes

- `scripts/*.py` harus accept `--json` flag dan output JSON ke stdout.
- Exit code 0 = success, non-zero = failure.
- Next.js wrapper `apps/web/src/lib/pythonRunner.ts` standardize call: timeout, env passing, error parsing.
- Tests untuk wrapper: mock spawn dengan fixed stdout/stderr/exitcode.

## References

- [ARCHITECTURE.md §2, §4](../ARCHITECTURE.md)
- [ADR-0003](ADR-0003-ui-framework.md)
- [ADR-0005](ADR-0005-llm-wrapper.md)
