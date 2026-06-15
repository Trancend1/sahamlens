# ADR-0020: Deployment & Platform Horizon (Boundary Only)

Status: Accepted (horizon boundary — no implementation)
Date: 2026-06-15
Builds on: ADR-0018 (agentic research layer boundary), ADR-0019 (agentic runtime, layer placement, audit), ADR-0001 (local-first), ADR-0004 (no broker credential).
Reference: `.insight/Early-Access-Registration-for-SumoPod.md` (insight only, not a commitment).

Accepted as a **horizon boundary only**. This ADR records a possible V3 platform direction and the limits around it. It binds nothing in V2. No container, multi-agent fleet, event bus, scheduler, object storage, or distributed architecture is approved for implementation by this ADR.

## Context

A SumoPod early-access/beta application (`.insight/Early-Access-Registration-for-SumoPod.md`) described a future where SahamLens becomes an "open-source agentic investment research platform": Hermes orchestrating a fleet of containerized agents (research, news, fundamental, technical, report generation, data-ingestion workers, cron jobs, future RAG/embedding pipelines), with S3-compatible object storage, a task-queue/event-bus execution model, horizontal per-agent scaling, and separation of API and worker layers.

This is a meaningfully different product shape from the locked identity. SahamLens today (CLAUDE.md / AGENTS.md, and 19 prior ADRs) is a **personal trading companion for one retail IDX trader**: local-first, public-repo-safe, single-user, non-advisory, manual-confirmation. ADR-0019 deliberately chose a **single local long-running process** with no scheduler, broker, or multi-process orchestration.

The owner reviewed the tension and decided: do not re-scope V2; capture the platform vision as a documented V3 horizon; preserve product identity and safety; and harvest only the benefits that add no scope.

## Decision

### 1. V2 is not re-scoped

The V2 agentic sprint plan in ADR-0019 (M0 outbound brief → M1 audit schema → M2 safe context → M3 tool contracts → M4 local Hermes runtime → M5 Discord deferred) stands unchanged. Nothing in this ADR alters those milestones or the locked stack.

### 2. Product identity is preserved and remains binding

These hold across any future platform work and may not be eroded by it:

- Personal companion for a **single** retail IDX trader. Not SaaS, not multi-user, not a public signal/advice service.
- **Local-first** and **public-repo-safe**: real private data stays in local private storage; nothing private is committed.
- **Non-advisory** and **manual-confirmation**: no buy/sell recommendation, no auto-execution, no autonomous trading action. Any agent is decision-support; the owner decides.

### 3. Safety hard-limits survive any platform move

The insight's language of "autonomous agents" and "scheduled market monitoring jobs" must not be read as permission to bypass ADR-0018. A future platform may run more processes, but:

- No agent may place orders, log into a broker, auto-execute a chat instruction, or act without explicit owner confirmation for write actions.
- "Scheduled jobs" in any future design are limited to data refresh / brief generation; they must not generate buy/sell signals or take trading actions.
- The AI response contract (evidence, freshness, caveats, uncertainty, source reference, non-financial-advice disclaimer) remains mandatory.

### 4. Harvest now — only zero-scope benefits

The following improve container/production readiness without adding scope, and are the only platform-influenced changes permitted in the current sprint horizon. They are guidance for M4 and adjacent work, not new milestones:

- **Env-driven config.** Runtime configuration (DB path, tokens, surface enablement) comes from environment / `.env.local`, never hardcoded. (`resolve_db_path` already follows this.)
- **Container-ready boundaries.** Keep `services/hermes` a self-contained runtime that imports `packages/core` and owns no business logic — already required by ADR-0019 D2.
- **Clean service separation.** Maintain the import rule (`core` must not import `services`/`scripts`/`web`) so a future split into independent services is mechanical, not a rewrite.

### 5. Everything else is deferred to a future technical ADR

If and when the owner pursues the platform direction, it requires its own technical ADR(s) and execution plan. Nothing below is approved here.

## Non-Goals (explicitly out of scope for V2 and this ADR)

- Containerization / SumoPod deployment, Dockerfiles, orchestration manifests.
- Multi-agent fleet (separate research/news/fundamental/technical/report services).
- Event bus, task queue, or workflow engine.
- Background scheduler / cron workers as a framework.
- S3-compatible object storage, embeddings store, RAG/document pipelines.
- Horizontal scaling, API/worker layer split, distributed execution.
- Any erosion of non-advisory / manual-confirmation / single-user / local-first identity.

## Deferred Technical ADR Topics (for a future V3 ADR, if pursued)

- Agent execution model: long-running services vs ephemeral jobs; queue vs workflow engine vs event bus.
- Per-agent concurrency and resource limits; which workloads warrant dedicated containers.
- Artifact persistence and retention: research reports, market snapshots, embeddings, financial documents, execution logs — including what may leave local storage and under what privacy rules.
- Observability: agent tracing, workflow monitoring, cost tracking, failure-recovery strategy.
- Secret management for a multi-service deployment.

## Consequences

Positive:

- The platform vision is captured so it is not lost, without destabilizing V2 or the locked identity.
- Container-readiness is preserved cheaply (config + boundaries already in place).
- Safety and privacy limits are explicitly carried into any future scaling.

Trade-offs:

- The distributed-platform questions remain open and unowned until a future ADR.
- Some SumoPod-implied capabilities (S3, multi-agent, scaling) are intentionally unavailable until then.

## Status of Open Questions

Recorded from the insight, **not decided here** — they belong to a future V3 technical ADR and must not be resolved unilaterally: agent execution model, concurrency/resource limits, artifact persistence/retention, observability, and multi-service secret management.

Implementation of any platform capability must not begin until a dedicated technical ADR and execution plan exist with owner approval.
