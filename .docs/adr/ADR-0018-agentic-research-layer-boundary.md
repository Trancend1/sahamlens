# ADR-0018: Agentic Research Layer Boundary

Status: Accepted
Date: 2026-06-12

Accepted as boundary-only. Technical process, logging schema, artifact storage, and redaction implementation are deferred to later ADRs/execution plans.

## Context

SahamLens is V1-ready as a local-first, single-user, decision-support tool. The owner has drafted a product proposal in `.docs/AGENTIC_RESEARCH_LAYER_PROPOSAL.md` that explores adding an agentic research layer using Hermes, Telegram, and Discord to reduce friction in the daily research workflow.

Current state:

- SahamLens is the trusted local data core and source of truth.
- Telegram is already used as optional delivery for alerts (ADR-0016).
- Earnings workflow is manual-first in V1-S6 (ADR-0017).
- Hermes is referenced as a personal agentic surface but is not yet integrated.
- No code, migration, schema, dependency, service, or command bot has been added for the agentic layer in this ADR.

Reference: `.docs/AGENTIC_RESEARCH_LAYER_PROPOSAL.md` (proposal only, not approved).

This ADR captures only the product and architecture boundary for that direction. All technical details (process model, schemas, migrations, services, dependencies, sprint plan) are intentionally out of scope here and must be addressed in a later ADR and execution plan.

## Decision

Adopt the SahamLens Agentic Research Layer as a product direction with the following boundary:

1. **SahamLens remains the trusted local data core.** Hermes is an orchestration layer that calls existing SahamLens capabilities through explicit tool contracts. It must not bypass SahamLens data quality or freshness rules, and it must not invent market facts independently.

2. **Chat surface priority.** Telegram is the first chat surface, focused on quick personal workflow. Discord is deferred as the second surface, used only for threaded private research, and only after Telegram value is proven.

3. **Default read-only.** Agentic interactions from Telegram or Discord default to reading SahamLens state. No write to the local DB is permitted without explicit manual confirmation in the same interaction.

4. **Write actions allowed, each with manual confirmation.** The only currently permitted write actions are: acknowledge alert, mark false positive, save journal draft, and add research queue item. Acknowledge and false-positive actions must reuse the existing V1-S6 alert lifecycle, not create a parallel lifecycle. Every other potential write remains out of scope for this ADR.

5. **Journal context is opt-in.** Opt-in granularity is per command or per session, default off. Ticker-level opt-in is deferred. The owner must explicitly allow journal context in any given chat interaction.

6. **Portfolio context is aggregate by default.** Default exposure sharing is aggregate only. Lot detail, average price, and P&L detail remain deferred and require explicit future owner approval.

7. **Non-advisory hard limit.** No buy or sell recommendation, no strong or weak language, no target price as instruction, no broker login, no order placement, no auto-execution, no copy trading, no public advice, and no advice for an audience or clients.

8. **AI response contract.** Every agentic response about a ticker, alert, journal item, or research item must include evidence, freshness, caveats, uncertainty, source reference, a non-financial-advice disclaimer, and a suggested next question.

9. **Privacy default.** Minimum necessary context. Private journal, portfolio, and research data must not be sent to the LLM or to a chat surface without explicit opt-in. Hermes journal access defaults to redacted or digest view only. Raw journal text requires explicit future opt-in. No private data is stored outside local private storage.

10. **Audit trail.** Agentic interactions must be auditable locally. The exact logging target (extending `ai_log` versus introducing a separate `agent_log`) is unresolved in this ADR and must be decided in a later ADR.

## Consequences

Positive:

- Product direction is captured without committing to any implementation.
- The boundary is explicit enough to prevent scope drift toward signal selling, broker integration, or auto-execution.
- Telegram and Discord roles are clearly separated and ordered.
- SahamLens local-first identity is preserved.
- Privacy and AI safety remain aligned with existing ADRs and `.docs/AI_BOUNDARIES.md`.

Trade-offs:

- Some owner expectations (for example, portfolio detail or automation) are intentionally deferred.
- Several open questions remain unresolved and need owner input before any execution plan can be written.
- The Hermes process boundary is not yet locked; technical ownership is still ambiguous.

## Non-Goals

- Broker integration, account sync, or order placement.
- Predictive trading AI, target price engine, or signal selling.
- Public recommendations, social or copy trading, community feeds.
- Auto-execution of any chat instruction.
- Public Discord channels or public advice for an audience.
- Migrations, schemas, services, dependencies, or code added in this ADR.
- A technical sprint plan or execution roadmap.
- Locking the unresolved questions listed below.

## Deferred Technical ADR Topics

The following technical topics are intentionally out of scope for this boundary ADR and must be addressed by a later technical ADR or execution plan:

- Hermes process boundary: external agent versus local sub-process wrapper.
- Logging target: extending `ai_log` versus introducing a separate `agent_log`.
- Research queue artifact schema and storage.
- Redaction and digest implementation for journal context.

## Unresolved Questions

The following questions come from `.docs/AGENTIC_RESEARCH_LAYER_PROPOSAL.md`. Some are partially resolved by this ADR boundary, others remain fully deferred to later technical ADRs or execution plans. They are recorded here so they are not lost, and they must not be decided unilaterally.

Partially resolved by this ADR boundary (implementation details still deferred):

4. Journal opt-in granularity: locked as per command or per session, default off. Ticker-level opt-in is deferred.
5. Portfolio opt-in detail: locked as aggregate exposure only. Lot detail, average price, and P&L detail remain deferred and require explicit future owner approval.
7. Alert acknowledge and false-positive lifecycle: locked to reuse the existing V1-S6 alert lifecycle. A parallel lifecycle is explicitly forbidden.
9. Hermes view of journal text: locked to default redacted or digest view. Raw journal text requires explicit future opt-in.

Fully deferred to later technical ADRs or execution plans:

1. Exact process boundary for Hermes: external agent versus local sub-process wrapper.
2. Logging target: extend `ai_log` versus introduce `agent_log`. Preference noted for a separate `agent_log` if interactions grow.
3. Research queue artifact schema and storage. Persistence of derived snapshots is approved at the boundary level, but schema and storage are deferred to a technical ADR.
6. Minimum useful daily Telegram brief content set. Proposal suggests watchlist changes, alerts, stale data, key news and earnings, and suggested research questions. Exact final set is deferred to execution plan.
8. Discord readiness criteria before enabling the second surface. Not defined.
10. Storage and retention policy for chat-derived drafts (journal drafts, research queue items). Deferred to execution plan.

Implementation must not begin until these are resolved by the owner or explicitly deferred with owner approval.
