# ADR-0019: Agentic Runtime, Layer Placement, and Audit Schema

Status: Accepted
Date: 2026-06-15
Supersedes: the blanket "long-running service" deferral in CLAUDE.md / AGENTS.md §3, scoped strictly to the local Hermes agent runtime.
Builds on: ADR-0018 (boundary), ADR-0016 (Telegram optional delivery), ADR-0013 (alert lifecycle), ADR-0005 (LLM wrapper).

This ADR resolves the technical questions ADR-0018 deferred (D0.1–D0.4). It is the technical counterpart to the boundary ADR. The product boundary, hard-no list, and AI response contract in ADR-0018 remain in force unchanged; this ADR only decides *how* the layer is built, *where* it lives, and *how* it is audited.

## Context

ADR-0018 accepted the Agentic Research Layer as a product direction but left four blockers unresolved and forbade implementation until the owner decided them:

1. Process boundary for Hermes (external agent vs local sub-process).
2. Audit logging target (`ai_log` vs `agent_log`).
3. Research queue artifact schema and storage.
4. Hermes layer placement within the locked 3-layer architecture (`core` / `scripts` / `web`).

A Critic review (2026-06-15) surfaced two issues that block any sprint plan:

- **C1 (Critical):** An interactive chat surface (`/brief`, `/ticker`, acknowledge/false-positive buttons) requires an inbound listener — a long-running process. Current Telegram support (`packages/core/alerts/telegram.py`) is outbound-only (`sendMessage`). CLAUDE.md §3 deferred "long-running service" entirely, so the product direction silently conflicted with the locked stack.
- **C2 (High):** `packages/core/ai/stock_chat.py` (`answer_stock_question`) and `generate_brief.py` (`generate_stock_brief`) already implement the AI response contract (RAG context, evidence with `source_ref`+`freshness`, caveats, `not_financial_advice`, budget check, circuit breaker, validator, `ai_log`). The proposal risked rebuilding this — making Hermes a "calculation engine kedua", which ADR-0018 §3 explicitly forbids.

The owner has authorized disruptive change to unblock the new direction, explicitly granting decisions D0.1–D0.4 and releasing the layer from stale stack constraints.

## Decision

### D1 — Process model: local long-running agent runtime via long-polling

Hermes runs as a **single local long-running process on the owner's machine**, using **outbound long-polling** (Telegram `getUpdates`; Discord gateway websocket when that surface is enabled later).

Rationale:

- **No inbound port, no public endpoint, no webhook, no tunnel.** Long-polling is an outbound HTTPS connection only. This preserves local-first and public-repo-safe identity better than a webhook server, and requires no firewall or DNS exposure.
- Single-user, single-process. No scheduler framework, no FastAPI sidecar, no message broker. The runtime is a plain Python process started by the owner (`uv run -m services.hermes`), and it may be stopped at any time without data loss.
- This is the minimum process model that satisfies the interactive surface in ADR-0018 §4. It scopes — and only scopes — the "long-running service" deferral to this one runtime.

Still deferred (not unlocked by this ADR): FastAPI sidecar, generic background scheduler, intraday/real-time alerting loop, any inbound HTTP server, multi-process orchestration.

The pull-only outbound brief (M0 below) does **not** require the runtime and ships first; the runtime is opt-in and additive.

### D2 — Layer placement: split pure tools (`core`) from the runtime adapter (`services/`)

The locked layer discipline (`core` = domain logic, no I/O orchestration; `web` = presentation; `scripts` = thin CLI orchestration) is preserved by splitting Hermes into two parts:

- **`packages/core/agent/`** — pure, testable, network-free. Holds: intent types, tool-contract definitions, the `safe context` boundaries (aggregate exposure, redacted journal digest), and response assembly that **delegates to existing `packages/core/ai`**. No sockets, no polling, no chat SDK imports.
- **`services/hermes/`** — a new top-level runtime layer. Holds the long-polling listener, chat-surface adapters (Telegram now, Discord later), intent routing, the policy gate, and write-action confirmation flow. It **imports `packages/core`; `packages/core` and `apps/web` must never import `services/`.**

`scripts/` keeps owning one-shot CLI orchestration (including M0's pull brief). The import rule is extended: `packages/core/*` must not import `apps/web/**`, `scripts/**`, or `services/**`.

This introduces `services/` as a new top-level concern in the repo. It is a deliberate, owner-approved structural change.

### D3 — Hermes must reuse `packages/core/ai`; it is not a second engine

Every agentic response about a ticker, alert, journal item, or research item **must** be produced by calling the existing `packages/core/ai` capabilities (`answer_stock_question`, `generate_stock_brief`, the alert explanation path, `validator`, `build_stock_context`). Hermes is forbidden from:

- re-implementing RAG context building,
- re-implementing the AI response contract / validation,
- calling the LLM provider directly outside the `core/ai` wrapper,
- inventing market facts or bypassing data-quality/freshness rules.

New `core/ai` surface may be *added* (e.g. an alert-explanation entry point, a research-queue summarizer) but the response contract, budget check, circuit breaker, and logging path are reused, not duplicated. This closes C2 and satisfies ADR-0018 Decision #1.

### D4 — Audit: dedicated `agent_log`, plus `agent_write_action` and `research_queue`

Introduce migration `0008_agent_runtime.sql` with three tables. `ai_log` is kept as-is for single LLM calls; agent interactions need fields `ai_log` does not have (surface, intent, session, write action, redaction status), so a separate table is correct rather than overloading `ai_log`.

- **`agent_log`** — one row per agent interaction:
  `id`, `session_id`, `surface` (`telegram`/`discord`/`cli`), `intent`, `command_text_redacted`, `ai_log_id` (nullable FK to the underlying `ai_log` call when one was made), `context_scope` (`none`/`aggregate`/`journal_digest`/...), `redaction_applied` (bool), `created_at`.
- **`agent_write_action`** — one row per write attempt, for confirmation + idempotency:
  `id`, `agent_log_id`, `action` (`acknowledge_alert`/`mark_false_positive`/`save_journal_draft`/`add_research_item`), `target_ref`, `idempotency_key` (unique), `status` (`pending_confirmation`/`confirmed`/`applied`/`rejected`/`expired`), `confirmed_at`, `created_at`. Acknowledge and false-positive actions write through the existing V1-S6 alert lifecycle (`packages/core/alerts/repo.py`) — no parallel lifecycle.
- **`research_queue`** — owner research items captured from chat:
  `id`, `ticker`, `note`, `source_surface`, `status` (`open`/`in_review`/`done`/`dropped`), `created_at`, `updated_at`. Stored in the local private DB only; never committed (`data/private/`).

Migration is forward + backward tested following `tests/test_migrate.py`. Stale local DBs must not break existing UX; the runtime status path stays read-only and additive (consistent with ADR-0017 carry-forward).

### D5 — Privacy and secrets carry forward unchanged

Aggregate-only portfolio exposure and redacted/digest journal context (ADR-0018 §6, §9) are implemented as pure `core/agent` boundaries with tests proving lot detail, average price, P&L, and raw journal text never enter an LLM or chat payload without explicit opt-in. Telegram secrets continue to follow the existing redaction pattern (`_safe_error_message` in `telegram.py`): never rendered, never logged, never committed.

## Consequences

Positive:

- C1 and C2 are resolved; a sprint plan can now be locked.
- Layer discipline survives a long-running runtime by separating pure tools (`core/agent`) from the adapter (`services/hermes`).
- Reuse of `core/ai` prevents engine duplication and keeps the AI safety contract single-sourced.
- Long-polling keeps the system local-first and repo-safe with no inbound exposure.
- Audit, idempotency, and research persistence have a concrete schema.

Trade-offs / accepted risks:

- `services/` is a new top-level layer; future agents must learn the extended import rule.
- A long-running process is now part of the system. Mitigation: opt-in, single-process, stoppable without data loss; M0 ships value without it.
- Discord remains undefined (ADR-0018 Q8) and out of scope here.

## Sprint Plan (locked)

Gate-0 is now satisfied (owner authorized D1–D4). Execution order, smallest-value-first:

| Milestone | Scope | Effort | Depends on | Acceptance |
|---|---|---|---|---|
| **M0 — Outbound brief (pull)** | `scripts/agent_brief.py` reusing `generate_stock_brief` + outbound Telegram (existing `telegram.py`). No runtime. | S (3–5d) | — | Brief carries disclaimer/freshness; passes anti-signal grep (`buy`/`sell`/`strong`/`target`); no residual process. |
| **M1 — Audit schema** | Migration `0008_agent_runtime.sql` (`agent_log`, `agent_write_action`, `research_queue`). | S (2–3d) | — | Forward+backward migrate green; stale-DB safe; no data loss. |
| **M2 — Safe context boundaries** | `packages/core/agent/`: `exposure_summary()` (aggregate-only), `journal_digest()` (redacted). | M (5–7d) | — | Tests prove lot/avg/P&L/raw-journal never in payload; default off. |
| **M3 — Tool contracts (read-only)** | `core/agent` tool layer wrapping `answer_stock_question`, `generate_stock_brief`, alert-explain, exposure/journal-digest. | M (5–8d) | M1, M2 | Typed contracts; all answers pass `validator`; no direct storage access from surface. |
| **M4 — Hermes runtime (interactive)** | `services/hermes/`: long-polling listener, intent routing, policy gate, write-action confirmation (idempotent, reuse alert lifecycle). | L (8–12d) | M3 | Write actions idempotent; secrets never rendered/logged; one `agent_log` row per interaction. |
| **M5 — Discord** | Deferred until Telegram value proven and ADR-0018 Q8 readiness criteria defined. | — | M4 proven | Not scheduled. |

## Non-Goals

- Webhooks, inbound HTTP server, public endpoints, tunnels.
- FastAPI sidecar, generic scheduler, multi-process orchestration.
- Anything in ADR-0018 Non-Goals (broker, order placement, predictive AI, public advice, auto-execution).
- Discord implementation.
- Raw journal text or portfolio lot/P&L detail to the LLM without explicit opt-in.

## Open Items

- ADR-0018 Q8 (Discord readiness criteria) still undefined — must be decided before M5.
- Retention policy for chat-derived drafts (ADR-0018 Q10) — decide during M2/M4; default: store in `data/private/`, owner-pruneable.
