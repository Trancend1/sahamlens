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
Current sprint: V1-S1 - Provider Health + Data Quality Foundation.

Critical path:

Data Quality -> Coverage/Fundamentals -> Screener -> Alerts

Start implementation from [.docs/EXECUTION_BLUEPRINT.md](.docs/EXECUTION_BLUEPRINT.md). Do not reopen product scope during implementation unless a real blocker appears.

## Sprint Log

| Sprint | Status | Branch / commit | Detail kecil | Kesulitan / catatan | Pending berikutnya |
|---|---|---|---|---|---|
| V1-S0 Docs Readiness | Done | `main` / `05a1a08`, `8ab8ee0` | Canonicalized `.docs`, added `AGENTS.md`, kept `CLAUDE.md` as pointer, locked ADR-0009 to ADR-0013. | Pre-commit line-ending hook tried to touch many files during all-files run; restored noise and committed only docs/alignment. | None for sprint start; main is ahead of origin until pushed. |
| V1-S1 Provider Health Foundation | Done | `v1/s1-provider-health-foundation` / `96939a5` | Added `packages/core/data_quality` with `ProviderHealthSnapshot`, `DataQualityOverview`, freshness states, trust tiers, source types, and focused tests. | Direct path pytest on `packages/core/data_quality/test_models.py` hit import-root quirk; full repo pytest passed and is the CI-like check. | Foundation model ready for CLI/UI consumers. |
| V1-S1 Schema / Migration | Done | `v1/s1-provider-health-foundation` / schema slice | Added `0003_provider_health.sql` plus repository upsert/list/overview helpers and migration-backed tests. | Mypy required hydrating DuckDB rows through `ProviderHealthSnapshot.model_validate` to preserve Literal validation. | Use repository from refresh CLI. |
| V1-S1 Provider Health CLI | Pending | Not started | Add refresh script using provider adapters and storing health snapshot. | Must not introduce realtime promises or extra providers. | Depends on provider health repository now available. |
| V1-S1 Data Quality UI Shell | Pending | Not started | Add dashboard shell and empty/fresh/stale/failed/partial/unknown states. | Must avoid duplicating business rules in React. | Depends on stable model/API shape. |

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
