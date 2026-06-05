# SahamLens Architecture

## Architecture Summary

SahamLens is a local-first single-user application.

- UI: Next.js dashboard in `apps/web`.
- Core: Python modules in `packages/core`.
- Storage: DuckDB file in `data/private`.
- Scripts: CLI entrypoints in `scripts`.
- AI: provider-agnostic wrapper in `packages/core/ai`.

Business logic belongs in `packages/core`. UI renders state and invokes local/API surfaces. Scripts orchestrate jobs but do not own domain logic.

## Locked Stack

| Layer | Decision |
|---|---|
| Web | Next.js 15 App Router, TypeScript strict, Tailwind, shadcn/ui |
| Core | Python 3.11+, strict typing |
| Database | DuckDB file-based local database |
| Charts | lightweight-charts |
| Tests | vitest, pytest, hypothesis |
| Lint/format | eslint, prettier, ruff, mypy |
| Package managers | pnpm and uv |
| AI | Provider-agnostic wrapper, no hardcoded vendor in feature modules |

Changing these requires an ADR.

## Module Boundaries

Expected core modules for V1:

- `packages/core/data_sources`: provider registry, fetch adapters, source metadata.
- `packages/core/data_quality`: provider health, freshness, coverage aggregation.
- `packages/core/fundamentals`: fundamental snapshots, completeness, confidence.
- `packages/core/screener`: transparent rule evaluation and result explanation.
- `packages/core/alerts`: local alert rules, events, feedback, quality tracking.
- `packages/core/earnings`: manual-first earnings event metadata and summaries.
- `packages/core/journal`: journal entries, weekly review, behavior summary.
- `packages/core/strategy`: simple named strategy rules, no DSL.
- `packages/core/ai`: prompt wrapper, safety validation, output schemas.
- `packages/core/schemas`: Pydantic models and migration definitions.
- `packages/core/runtime`: local runtime readiness, migration status, missing table checks, and bootstrap status models.

Rules:

- `packages/core/*` must not import from `apps/web` or `scripts`.
- `scripts/*` may call core modules.
- `apps/web` may call APIs or read prepared local outputs, but should not duplicate business rules.
- Data model changes require tests and migration review.

## Data Model Areas

V1 schema should cover:

- Provider health.
- Source coverage.
- Ticker lifecycle status.
- Fundamental snapshots.
- Fundamental completeness/confidence.
- Screener rules and results.
- Alert rules, events, and feedback.
- Earnings metadata.
- Weekly journal review.
- Simple strategy rules.

Schema should store source, fetched/imported timestamp, freshness status, and confidence where decisions depend on data quality.

## CLI and Script Surfaces

Candidate scripts:

- Inspect local runtime readiness.
- Bootstrap local runtime safely.
- Refresh provider health.
- Refresh ticker universe coverage.
- Ingest fundamental snapshots.
- Run screener.
- Evaluate alerts.
- Record alert feedback.
- Create earnings summary.
- Generate weekly journal review.

Scripts should be idempotent where practical and safe to run manually.

## V1-S6 Alert and Earnings Boundary

V1-S6 keeps the same local CLI-backed runtime. Alerts and earnings do not introduce
FastAPI, a background service, a scheduler, or a daemon.

Alert boundary:

- Alert evaluation is manually invoked through CLI/API surfaces.
- Local alert events are the source of truth.
- Alert events must store freshness, confidence, rule context, caveats, and review state.
- False-positive feedback is quality tracking only; it is not predictive labeling.
- Telegram delivery is optional and can only happen after a local alert event exists.
- Telegram delivery failure must not delete or invalidate the local alert event.
- Telegram delivery is explicit/manual in V1-S6; no background service sends alerts.
- Telegram secrets are env-based and redacted from CLI/UI output.

Earnings boundary:

- Earnings events are manual-first.
- Summaries use available local/manual input and must show caveats and confidence.
- Automated unreliable scraping is out of scope for V1-S6.
- Earnings output supports post-event review and must not produce buy/sell judgment.
- Earnings UI is a local `/earnings` page backed by `scripts.earnings`; it does not
  fetch network data during render.

## Local Runtime Contract

V1 remains CLI-backed and local-first. It does not introduce FastAPI or a long-running
service.

The runtime contract is:

- `uv run python -m scripts.runtime status --json` reports `ok`, `status`,
  `db_path`, `python_executable`, `applied_migrations`, `pending_migrations`,
  `missing_tables`, `schema_status`, `warnings`, `errors`, and
  `recommended_commands`.
- `uv run python -m scripts.runtime bootstrap --json` safely applies migrations and then
  attempts local data bootstrap steps only when their prerequisites exist. Optional data
  refresh failures are warnings, not fatal errors.
- `uv run python -m scripts.migrate` remains the immediate recovery command for stale
  schema or missing migration tables.
- `status` is read-only. Real local DB mutation must be an explicit developer action via
  `scripts.migrate` or `scripts.runtime bootstrap`; tests use temporary DuckDB fixtures.
- Web fetchers must translate Python/DuckDB failures into structured runtime errors:
  `schema_stale`, `missing_table`, `python_not_found`, `db_locked`, `empty_data`, or
  `command_failed`.
- UI surfaces must show recovery states instead of raw tracebacks.
- FastAPI, background jobs, progress streaming, and port/service lifecycle are deferred
  to V1.5/V2 unless CLI process overhead becomes a proven blocker.

Windows web dev fallback:

```powershell
$env:PYTHON_BIN=(Resolve-Path ".venv/Scripts/python.exe").Path
pnpm.cmd --filter @sahamlens/web dev
```

## UI and Route Surfaces

V1 pages/components:

- Data Quality Dashboard.
- Fundamental Snapshot card.
- Screener page.
- Alerts page.
- Earnings page.
- Weekly Journal Review page.
- Strategy Rules page.

UI must show freshness, source, confidence, and caveats before enabling dependent actions.

## Freshness and Confidence Mechanics

Freshness states:

- Fresh: data inside accepted window.
- Delayed: expected lag but still usable with caveat.
- Stale: outside accepted window; dependent flows restricted.
- Failed: latest fetch failed; show error and last successful timestamp.
- Partial: some required sources/fields missing.
- Unknown: no reliable timestamp/source.

Confidence inputs:

- Coverage score.
- Freshness score.
- Provider trust score.
- Completeness score.

Confidence affects Fundamental Snapshot labels, screener eligibility, alert evaluation, and AI caveats.

## Migration Rules

- No migration without a ticket and schema tests.
- Keep migrations small and reversible where possible.
- Do not store private market notes or portfolio data in committed sample files.
- Use fake sample data only in `data/sample`.

## AI Boundary in Architecture

AI features can summarize, explain, critique, and ask clarifying questions. AI features cannot:

- Produce buy/sell/hold commands.
- Predict exact future price as fact.
- Approve a trade plan.
- Hide missing data or stale sources.

See [AI_BOUNDARIES.md](AI_BOUNDARIES.md).

## Anti-Scope Architecture

V1 must not introduce:

- Broker integration.
- Realtime market data infrastructure.
- Multi-user/auth/billing.
- Vector database.
- Microservice split.
- Strategy DSL.
- Social sentiment pipeline.
