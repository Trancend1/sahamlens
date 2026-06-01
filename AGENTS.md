# AGENTS.md - SahamLens

SahamLens is a personal trading companion for one retail IDX trader. It is local-first, public-repo-safe, and AI-assisted. AI explains; the user decides.

This file is an agent alignment layer. Product and technical facts live in `.docs/`.

## Documentation Map

Always cite or edit the canonical file instead of duplicating facts here.

| Topic | Source of truth |
|---|---|
| Product scope, goals, non-goals | [.docs/PRD.md](.docs/PRD.md) |
| Execution roadmap, sprint, backlog | [.docs/EXECUTION_BLUEPRINT.md](.docs/EXECUTION_BLUEPRINT.md) |
| System architecture and module boundaries | [.docs/ARCHITECTURE.md](.docs/ARCHITECTURE.md) |
| Data providers, freshness, coverage, confidence | [.docs/DATA_SOURCES.md](.docs/DATA_SOURCES.md) |
| AI rules and output boundaries | [.docs/AI_BOUNDARIES.md](.docs/AI_BOUNDARIES.md) |
| Privacy, secrets, and threat model | [.docs/SECURITY.md](.docs/SECURITY.md) |
| Trading disclaimer copy and placement | [.docs/TRADING_DISCLAIMER.md](.docs/TRADING_DISCLAIMER.md) |
| UI rules and visual vocabulary | [.docs/DESIGN_SYSTEM.md](.docs/DESIGN_SYSTEM.md) |
| Engineering workflow | [.docs/ENGINEERING_STANDARDS.md](.docs/ENGINEERING_STANDARDS.md) |
| Contribution process | [.docs/CONTRIBUTING.md](.docs/CONTRIBUTING.md) |
| Long-lived technical decisions | [.docs/adr/](.docs/adr/) |

Rules:

- Before claiming a fact, check the relevant source-of-truth doc.
- Before changing a fact, edit the canonical doc.
- Before creating a new doc, check whether it belongs in an existing doc.
- Keep planning history out of active docs unless the owner explicitly asks for an archive.

## Current Phase

Phase: V1 - Better Decision Support.
Planning status: frozen.
Current sprint: V1-S3 - Screener.

Critical path:

Data Quality -> Coverage/Fundamentals -> Screener -> Alerts

Start implementation from [.docs/EXECUTION_BLUEPRINT.md](.docs/EXECUTION_BLUEPRINT.md). Do not reopen product scope during implementation unless a real blocker appears.

## Sprint Log

| Sprint | Status | Branch / commit | Detail kecil | Kesulitan / catatan | Pending berikutnya |
|---|---|---|---|---|---|
| V1-S0 Docs Readiness | Done | `main` / `05a1a08`, `8ab8ee0` | Canonicalized `.docs`, added `AGENTS.md`, kept `CLAUDE.md` as pointer, locked ADR-0009 to ADR-0013. | Pre-commit line-ending hook tried to touch many files during all-files run; restored noise and committed only docs/alignment. | None for sprint start; main is ahead of origin until pushed. |
| V1-S1 Provider Health Foundation | Done | `v1/s1-provider-health-foundation` / `96939a5` | Added `packages/core/data_quality` with `ProviderHealthSnapshot`, `DataQualityOverview`, freshness states, trust tiers, source types, and focused tests. | Direct path pytest on `packages/core/data_quality/test_models.py` hit import-root quirk; full repo pytest passed and is the CI-like check. | Foundation model ready for CLI/UI consumers. |
| V1-S1 Schema / Migration | Done | `v1/s1-provider-health-foundation` / schema slice | Added `0003_provider_health.sql` plus repository upsert/list/overview helpers and migration-backed tests. | Mypy required hydrating DuckDB rows through `ProviderHealthSnapshot.model_validate` to preserve Literal validation. | Use repository from refresh CLI. |
| V1-S1 Provider Health CLI | Done | `v1/s1-provider-health-foundation` / current slice | Added `scripts.provider_health` with `list` and `refresh-yfinance`, JSON output, yfinance snapshot mapping, and CLI tests. | Kept UI reads separate from refresh so dashboard render does not hit yfinance/network. | Richer provider history deferred until dogfooding shows it is needed. |
| V1-S1 Data Quality UI Shell | Done | `v1/s1-provider-health-foundation` / current slice | Added `/data-quality`, `fetchDataQualityOverview`, dashboard summary cards, provider cards, empty/error state, and all six freshness states. | Existing `FreshnessBadge` still uses legacy `fresh/stale/old`; V1 data-quality UI uses new explicit states separately. | None for S1; watch legacy freshness naming during S2 integration. |
| V1-S1 Dogfood + Local Refresh | Done | `v1/s1-provider-health-foundation` / local DB | Ran migration, confirmed empty overview, refreshed yfinance for `BBCA.JK` and `TLKM.JK`, and persisted a fresh snapshot with coverage `2`. | Requires network availability; yfinance remains Tier 3 and must keep caveat visibility. Local DB is ignored at `data/private/sahamlens.duckdb`. | V1-S1 ready for review/PR; next implementation should begin V1-S2 after merge. |
| V1-S2 Sprint Prep | Done | `v1/s2-ticker-fundamental-snapshot` / `cad43e2` | Prepared vertical slice for ticker lifecycle, coverage tiers, and lightweight fundamental snapshot with confidence. | Must reuse V1-S1 Data Quality as prerequisite and avoid reopening frozen product scope. | ADR readiness confirmed; proceed to schema/migration with tests. |
| V1-S2 ADR Readiness | Done | `v1/s2-ticker-fundamental-snapshot` / readiness slice | Confirmed ADR-0011 covers lifecycle/coverage and ADR-0012 covers fundamental completeness/confidence. | Implementation vocabulary is locked: active/suspended/delisted/renamed/unknown, tier_a/tier_b/tier_c, complete/partial/sparse/missing, high/medium/low/none. | Schema must store source, timestamps, missing fields, caveat/reason text, and avoid predictive scores. |
| V1-S2 Schema / Migration | Done | `v1/s2-ticker-fundamental-snapshot` / schema slice | Added DuckDB schema for ticker lifecycle status, source coverage, fundamental snapshots, missing fields, completeness, confidence, source, and fetched/imported timestamps. | Kept migration narrow; no financial terminal scope, no automated IDX parser, and no predictive scoring. | Next: implement coverage repository/classifier and fundamental snapshot models. |
| V1-S2 Coverage Core | Done | `v1/s2-ticker-fundamental-snapshot` / coverage slice | Implemented coverage classifier for Tier A/B/C and lifecycle states: active, suspended, delisted, renamed, unknown. | Screener/alert eligibility stays conservative for stale, failed, partial, unknown, suspended, delisted, or unmapped renamed tickers. | Next: connect fundamental snapshots into coverage/fundamental CLI flows. |
| V1-S2 Fundamental Snapshot Core | Done | `v1/s2-ticker-fundamental-snapshot` / fundamental slice | Implemented lightweight fundamental snapshot model, ingestion builder, completeness calculation, confidence calculation, and DuckDB repository. | Public-provider/manual fundamentals preserve missing fields and confidence caveats; no predictive score or financial-terminal scope. | Next: expose coverage/fundamental flows through CLI. |
| V1-S2 CLI | Done | `v1/s2-ticker-fundamental-snapshot` / CLI slice | Added `scripts.fundamentals` commands to ingest/list fundamental snapshots, refresh/list ticker coverage, and show combined symbol snapshot. | CLI orchestrates only; classifier/completeness/confidence logic stays in `packages/core`. UI reads local snapshots and does not refresh network during render. | Next: add Fundamental Snapshot card and coverage/lifecycle badges in web UI. |
| V1-S2 UI | Done | `v1/s2-ticker-fundamental-snapshot` / UI slice | Added Fundamental Snapshot card, coverage/lifecycle badges, completeness/confidence badges, caveats, empty state, and read-only state when incomplete. | UI renders core-provided states via `scripts.fundamentals snapshot`; no classifier logic or network refresh runs during render. | Next: dogfood watchlist tickers and verify full S2 sprint. |
| V1-S2 Dogfood | Done | `v1/s2-ticker-fundamental-snapshot` / local DB | Reviewed watchlist coverage and fundamental snapshots after local ingest/refresh. `BBCA.JK` resolved Tier A with partial/medium fundamentals; `TLKM.JK` stayed Tier C with sparse/low fundamentals because OHLCV coverage is missing locally. | DuckDB local file can lock when multiple CLI commands read/write in parallel; run dogfood refresh/read commands sequentially. | V1-S2 implemented and verified; next sprint can begin after review/PR merge. |
| V1-S2 Verification | Done | `v1/s2-ticker-fundamental-snapshot` / verification slice | Full S2 verification passed: Python tests/type/lint/format, web tests/type/lint/build, migration idempotency, CLI ingest/list/snapshot/coverage dogfood. | Existing non-blocking warnings remain: Vite CJS API deprecation, `next lint` deprecation, and Next `experimental.typedRoutes` warning. | Prepare PR summary and move to V1-S3 only after merge. |
| V1-S3 Sprint Prep | Done | `v1/s3-screener` / prep slice | Prepared transparent screener vertical slice that consumes V1-S1 Data Quality and V1-S2 Coverage/Fundamental confidence gates. | Must not introduce signal language, recommendations, prediction, or hidden scoring. | Next: write/confirm Screener semantics ADR before schema work. |
| V1-S3 ADR Readiness | Done | `v1/s3-screener` / ADR slice | Added ADR-0014 Screener Semantics and locked transparent filter language, rule gates, result states, and exclusion behavior. | Screener language must remain filter/explain/exclude, never buy/sell/hold or candidate recommendation. | Schema must encode required fields, freshness/confidence gates, run metadata, results, exclusions, and caveats. |
| V1-S3 Schema / Migration | Done | `v1/s3-screener` / schema slice | Added DuckDB schema for screener rules, rule conditions, runs, results, exclusions, required fields, freshness/confidence gates, and run metadata. | Kept rules transparent and local; no strategy DSL and no predictive scoring. | Next: implement `packages/core/screener` evaluator against these tables. |
| V1-S3 Screener Core | Done | `v1/s3-screener` / core slice | Implemented transparent evaluator that applies explicit rules to local ticker coverage, fundamentals, optional price/indicator fields, freshness states, and confidence gates. | Result copy stays filter/exclude/caveat only; no signal language. Direct path pytest still has package-root quirks, so full repo pytest is the reliable check. | Next: expose saved/built-in rule execution through CLI. |
| V1-S3 CLI | Done | `v1/s3-screener` / CLI slice | Added `scripts.screener run` for saved or built-in rules, watchlist/symbol input, explainable JSON output, and persisted run/results. | CLI orchestrates only and reads local DuckDB; it does not call AI or external network during screener evaluation. | Next: add Screener page that renders core-provided explanations and exclusion reasons. |
| V1-S3 UI | Done | `v1/s3-screener` / UI slice | Added `/screener`, rule summary, result table, exclusion reasons, freshness/confidence/completeness badges, empty state, and error state. | UI renders core-provided explanations and does not duplicate evaluator logic in React. | Next: run full S3 verification and tighten no-signal test coverage. |
| V1-S3 Tests | Done | `v1/s3-screener` / verification slice | Added Python core/repo/CLI tests and web lib/component tests for eligibility gates, stale behavior, missing fields, Tier C exclusions, lifecycle exclusions, and no-signal copy. | Full verification passed; existing non-blocking warnings remain: Vite CJS API deprecation, `next lint` deprecation, and Next `experimental.typedRoutes` warning. | Next: dogfood against local watchlist after owner wants S3 dogfood/run-through. |
| V1-S3 Dogfood | Pending | Not started | Run screener against local watchlist and review included/excluded tickers with reasons. | Success means transparent filtering and caveats, not profitable signals. | Dogfood after migration, core, CLI, and UI are verified. |

## Scope Guardrails

Allowed V1 work:

- Data Quality Dashboard.
- Provider Health.
- Ticker lifecycle and coverage.
- Fundamental Snapshot with completeness/confidence.
- Screener with transparent no-signal language.
- Local alert rules/events with false-positive feedback.
- Weekly Journal Review.
- Simple Strategy Rules.
- Earnings Summary manual-first.

Out of scope for V1:

- Broker login, cookies, sessions, account sync, or order placement.
- Realtime or tick-data promise.
- Predictive AI, AI buy/sell alerts, or forecasting alerts.
- Public recommendations, signal selling, SaaS, auth, billing, or multi-user scope.
- Automated IDX crawling.
- Full news article storage or republication.
- Strategy DSL.

## Stack

Locked stack:

- UI: Next.js 15 App Router, TypeScript strict, Tailwind, shadcn/ui.
- Core: Python 3.11+ with strict typing.
- DB: DuckDB local file.
- Charts: `lightweight-charts`.
- Tests: `vitest`, `pytest`, `hypothesis`.
- Lint/format: `eslint`, `prettier`, `ruff`, `mypy`.
- Package managers: `pnpm`, `uv`.
- AI: provider-agnostic wrapper in `packages/core/ai`.

Changing the stack requires an ADR.

## Engineering Rules

- Keep business logic in `packages/core`.
- Keep `scripts` as orchestration only.
- Keep `apps/web` presentation-focused.
- `packages/core/*` must not import `apps/web/**` or `scripts/**`.
- Use strict TypeScript and strict Python typing.
- Avoid `any` and `# type: ignore` unless a short why is included.
- Add tests for changed behavior.
- Do not commit private data from `data/private/*`.
- Prefer small vertical PRs.
- Use conventional commits.

## AI Rules

AI may:

- Summarize evidence.
- Explain caveats.
- Critique a user-written plan.
- Generate reflection and review.
- Redact private context before LLM use.

AI must not:

- Say buy, sell, hold, strong buy, safe, guaranteed, or equivalent signal language.
- Predict exact future prices as fact.
- Approve a trade plan.
- Auto-execute anything.
- Generate public recommendations or client-facing signal content.

Product AI output must include non-empty `evidence`, non-empty `caveats`, and `not_financial_advice: true`. See [.docs/AI_BOUNDARIES.md](.docs/AI_BOUNDARIES.md).

## Communication

- Bahasa Indonesia by default unless the user switches.
- Be concise and direct.
- Cite files with paths.
- If data is insufficient, say so.
- Do not claim completion before relevant verification passes or limitations are stated.

## Contribution Identity

- Do not add `Co-Authored-By: Codex` or other AI co-author trailers.
- Do not add generated-with-AI metadata to commits or PRs.
- Use the repo owner's git identity.
- AI is a ghostwriter; the owner is the author.

## Repo Mental Model

```text
apps/web/          Next.js dashboard
packages/core/     Python data core
  data_sources     providers and source metadata
  data_quality     provider health, freshness, coverage
  fundamentals     snapshots, completeness, confidence
  screener         transparent rules and results
  alerts           local rules, events, feedback
  earnings         manual-first earnings metadata
  journal          entries and weekly review
  strategy         simple rules, no DSL
  ai               LLM wrapper and validation
  schemas          Pydantic models and migrations
scripts/           CLI orchestration
data/sample/       fake committed data
data/private/      ignored real local data
prompts/system/    versioned prompt templates
config/            example config committed, local config ignored
.docs/             canonical documentation
```

End of AGENTS.md.
