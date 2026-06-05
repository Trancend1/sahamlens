# SahamLens Execution Blueprint

## Status

V1 planning is frozen. V1-S6 is implementation-complete on the current feature branch and ready for release readiness review.

Current phase: Phase V1 - Better Decision Support.
Current sprint: V1-S6 - Completed.
Next step: Release readiness / PR review.

Implementation must follow the critical path:

Data Quality -> Coverage/Fundamentals -> Screener -> Journal/Strategy -> Polish Gate -> Alerts/Earnings

## Planning Freeze

V1 planning is closed. This file keeps only execution-critical scope, roadmap, backlog index, gates, and first PR order. Historical planning notes are intentionally removed from active docs.

## V1 Scope Lock

Core:

- Data Quality Dashboard.
- Provider Health.
- Ticker lifecycle and coverage model.
- Fundamental Snapshot with completeness/confidence.
- Screener.
- Local alert rules/events with false-positive feedback.
- Weekly Journal Review.
- Simple Strategy Rules.
- Earnings Summary manual-first.

Optional:

- Telegram notifications.
- Market-hours delayed/indicative refresh.
- Extra validated RSS feeds.
- Provider-ready LLM internals.
- RSS-backed earnings event discovery.

Deferred or experimental:

- Intraday snapshot.
- Backtesting-lite.
- Performance analytics beyond weekly review.
- Automated IDX filing/parser pipeline.
- Social sentiment streams.

Rejected:

- Realtime/tick-data promise.
- Predictive or AI buy/sell alerts.
- Broker integration.
- Automated IDX crawling for V1.
- Public recommendations, SaaS, or multi-user scope.
- Strategy DSL.
- Full news article storage/republication.

## Mandatory ADRs Before Coding

The first implementation PR must not start until these decisions are written or confirmed as existing ADRs:

1. Provider Health as prerequisite: [ADR-0009](adr/ADR-0009-provider-health-prerequisite.md).
2. OHLCV freshness contract: [ADR-0010](adr/ADR-0010-ohlcv-freshness-contract.md).
3. Ticker lifecycle and coverage model: [ADR-0011](adr/ADR-0011-ticker-lifecycle-coverage-model.md).
4. Fundamental completeness and confidence: [ADR-0012](adr/ADR-0012-fundamental-completeness-confidence.md).
5. Alert lifecycle and false-positive tracking: [ADR-0013](adr/ADR-0013-alert-lifecycle-false-positive-tracking.md).
6. Telegram optional delivery: [ADR-0016](adr/ADR-0016-telegram-optional-delivery.md).
7. Earnings manual-first summary: [ADR-0017](adr/ADR-0017-earnings-manual-first-summary.md).

Can be written during the related sprint:

- Screener semantics.
- News metadata-only boundary.
- Simple strategy rules and no DSL.
- Provider-ready LLM direction.

## Sprint Roadmap

| Sprint | Theme | Goal | Usable after sprint |
|---|---|---|---|
| V1-S1 | Provider Health + Data Quality Foundation | Make data trust visible before building dependent features. | User can inspect provider health, freshness, coverage, stale counts, and failed fetches. |
| V1-S2 | Ticker Lifecycle + Fundamental Snapshot | Add coverage tiers and lightweight fundamentals with confidence. | User can review supported tickers and fundamental snapshots with caveats. |
| V1-S3 | Screener | Run transparent filters using freshness and confidence gates. | User can screen candidates without signal language or hidden assumptions. |
| V1-S4 | Weekly Journal Review + Strategy Rules | Convert journal history into behavior review and simple rule checks. | User can review weekly behavior and rule violations. |
| V1-S5 | Polish + Runtime Readiness + UX Stabilization | Make the existing V1 experience consistent, actionable, and safe for daily local use. | User can navigate core pages with clear empty/error/loading states and runtime recovery guidance. |
| V1-S6 | Alerts + Telegram Optional + Earnings Summary | Add local alert lifecycle and manual-first earnings workflow after the V1 UX polish gate. | User can receive/review local alerts, track false positives, and summarize earnings events. |

## Dependency Matrix

| Sprint | Blocked by | Enables | Parallelizable |
|---|---|---|---|
| V1-S1 | None | V1-S2, V1-S3, V1-S5 | UI shell, provider registry, docs cleanup |
| V1-S2 | V1-S1 | V1-S3, V1-S5 | Fundamental UI and lifecycle schema can be split |
| V1-S3 | V1-S1, V1-S2 | V1-S5 | Screener UI and rule fixtures |
| V1-S4 | Existing journal baseline | V1-S5 | Can run parallel after V1-S1 |
| V1-S5 | V1-S1, V1-S2, V1-S3, V1-S4, runtime contract | V1-S6 | Copy, empty states, responsive polish, and docs can be split |
| V1-S6 | V1-S5, ADR-0013 | V1 exit | Telegram optional and earnings manual path can be split |

## Sprint Backlog Index

Backlog is intentionally ticket-sized and implementation-ready. Ticket details should live in the issue tracker or PR descriptions when execution starts.

### V1-S1

- ADR-S1-01: Provider Health prerequisite ADR.
- ADR-S1-02: OHLCV freshness contract ADR.
- SCHEMA-S1-01: Provider health and freshness models.
- CORE-S1-01: Provider health collector.
- CORE-S1-02: Data quality aggregation.
- CLI-S1-01: Refresh provider health.
- UI-S1-01: Data Quality Dashboard shell.
- TEST-S1-01: Provider health and freshness tests.
- DOGFOOD-S1: Daily data-quality review.

### V1-S2

- ADR-S2-01: Ticker lifecycle and coverage ADR.
- ADR-S2-02: Fundamental completeness/confidence ADR.
- SCHEMA-S2-01: Ticker lifecycle and source coverage models.
- SCHEMA-S2-02: Fundamental snapshot model.
- CORE-S2-01: Coverage classifier.
- CORE-S2-02: Fundamental snapshot ingestion.
- CLI-S2-01: Refresh ticker coverage.
- CLI-S2-02: Ingest fundamentals.
- UI-S2-01: Fundamental Snapshot card.
- TEST-S2-01: Coverage and confidence tests.
- DOGFOOD-S2: Watchlist fundamental review.

### V1-S3

- ADR-S3-01: Screener semantics ADR.
- SCHEMA-S3-01: Screener rules and results.
- CORE-S3-01: Screener evaluator.
- CLI-S3-01: Run screener.
- UI-S3-01: Screener page.
- TEST-S3-01: Screener eligibility and stale behavior tests.
- DOGFOOD-S3: Candidate filter review.

### V1-S4

- ADR-S4-01: Simple strategy rules/no DSL ADR.
- SCHEMA-S4-01: Weekly review and strategy-rule models.
- CORE-S4-01: Weekly journal review generator.
- CORE-S4-02: Simple strategy-rule checker.
- CLI-S4-01: Generate weekly journal review.
- UI-S4-01: Weekly Journal Review page.
- UI-S4-02: Strategy Rules page.
- TEST-S4-01: Journal and rule tests.
- DOGFOOD-S4: Weekly behavior review.

### V1-S5

- UI-S5-01: Dashboard and navigation polish.
- UI-S5-02: Shared actionable empty/error/loading states.
- UI-S5-03: Runtime readiness recovery copy across dependent pages.
- UI-S5-04: Table overflow and responsive layout wrappers.
- COPY-S5-01: No-signal, no-profit-promise copy audit.
- TEST-S5-01: Empty/error/healthy state regression tests.
- DOC-S5-01: Roadmap update with alerts deferred to V1-S6.
- DOGFOOD-S5: Daily local use walkthrough across Dashboard, Data Quality, Screener, Journal, Weekly Review, Strategy Rules, Watchlist, and Portfolio.

### V1-S6

- PLAN-S6-01: Scope lock, ADR, data contract, CLI/UI boundary, and test plan.
- ADR-S6-01: Alert lifecycle and false-positive tracking ADR update.
- ADR-S6-02: Telegram optional delivery ADR.
- ADR-S6-03: Earnings manual-first summary ADR.
- SCHEMA-S6-01: Proposed `0007_alerts_earnings.sql` for alert rules, evaluations, events, delivery attempts, earnings events, and earnings summaries.
- CORE-S6-01: Alert evaluator.
- CORE-S6-02: Alert feedback and quality tracking.
- CORE-S6-03: Earnings summary manual workflow.
- CLI-S6-01: Evaluate alerts.
- CLI-S6-02: Record alert feedback.
- CLI-S6-03: Create earnings summary.
- UI-S6-01: Alerts page.
- UI-S6-02: Earnings Summary section.
- OPTIONAL-S6-01: Telegram notification sender.
- TEST-S6-01: Alert lifecycle and false-positive tests.
- DOGFOOD-S6: Alert and earnings review.

## V1-S6 Scope Lock and Data Contract

V1-S6 adds local alert lifecycle, optional Telegram delivery, and manual-first earnings summary. This section is planning and contract only; implementation starts in V1-S6-02.

### Final V1-S6 Scope

Local Alert Lifecycle:

- Alert definitions with active, paused, and archived states.
- Manual alert evaluations through CLI-backed local runtime.
- Alert events with review states, evidence, source/freshness context, and caveats.
- Acknowledged, dismissed, marked false-positive, and resolved event handling.
- False-positive tracking as quality feedback, not model training.
- Stale-data and low-confidence protection before alert events are created.
- CLI command to evaluate alerts manually.
- UI page or section to review alert rules, event history, and feedback.

Telegram Optional:

- Optional delivery channel only, disabled by default.
- Local config/env-based setup.
- No hard dependency for local alert rules or event review.
- Alert events must exist locally before Telegram delivery is attempted.
- Bot token and chat id must never be rendered, logged, or stored in plain UI output.
- Delivery failure is stored as a warning/error on the delivery attempt, not as alert failure.
- No background daemon, scheduler, or long-running service in V1-S6.

Manual-First Earnings Summary:

- User can manually create, import, or register an earnings event.
- User can attach notes or summary input.
- Summary is generated from available local/manual data.
- Summary must include caveats, source type, and confidence.
- No prediction, no buy/sell judgment, and no unreliable automated scraping.
- Output supports post-event review, not trade recommendation.

### V1-S6 Non-Scope

- Realtime or intraday alerting.
- Always-on background scheduler.
- Broker integration, account sync, order placement, or auto-trading.
- Push notification service beyond optional Telegram.
- Cloud sync, multi-user auth, SaaS, billing, or public recommendations.
- FastAPI sidecar or long-running service.
- Financial advice, buy/sell signal, guaranteed/profit language.
- Automatic earnings scraping from unreliable sources.
- Alert recommendations that promise profit or future price direction.

### Proposed Migration

Migration proposal only: `0007_alerts_earnings.sql`.

`alert_rules`:

- `id`, `name`, `description`, `rule_type`, `ticker`, `parameters_json`, `is_active`, `created_at`, `updated_at`, `archived_at`.

`alert_evaluations`:

- `id`, `rule_id`, `evaluated_at`, `status`, `reason`, `data_freshness_status`, `confidence_status`, `matched`, `details_json`.

`alert_events`:

- `id`, `rule_id`, `evaluation_id`, `ticker`, `event_type`, `severity`, `title`, `message`, `status`, `created_at`, `acknowledged_at`, `dismissed_at`, `false_positive_at`, `resolved_at`, `notes`.

`alert_delivery_attempts`:

- `id`, `event_id`, `channel`, `status`, `attempted_at`, `error_code`, `error_message`, `redacted_details_json`.

`earnings_events`:

- `id`, `ticker`, `period`, `event_date`, `source_type`, `source_ref`, `status`, `created_at`, `updated_at`, `notes`.

`earnings_summaries`:

- `id`, `earnings_event_id`, `generated_at`, `summary_text`, `caveats`, `input_snapshot_json`, `confidence_status`.

Before implementation, confirm no existing migration already owns these names.

### CLI Contract Proposal

Alerts:

```bash
uv run python -m scripts.alerts --json rules list
uv run python -m scripts.alerts --json rules create
uv run python -m scripts.alerts --json evaluate
uv run python -m scripts.alerts --json events list
uv run python -m scripts.alerts --json events acknowledge --event-id <id>
uv run python -m scripts.alerts --json events mark-false-positive --event-id <id>
```

Telegram optional:

```bash
uv run python -m scripts.alerts --json telegram status
uv run python -m scripts.alerts --json telegram test
```

Earnings:

```bash
uv run python -m scripts.earnings --json events list
uv run python -m scripts.earnings --json events create
uv run python -m scripts.earnings --json summary generate --event-id <id>
```

CLI implementation must follow existing script style: JSON output for web consumption, core logic in `packages/core`, and no provider/network work during UI render.

### UI Contract Proposal

Potential surfaces:

- Alerts page.
- Alert detail/review drawer.
- Alert rule form.
- Alert event history.
- Telegram settings/status panel.
- Earnings events page or section.
- Earnings summary detail.

Required states:

- No alerts configured.
- No alert events yet.
- Alert evaluation skipped because data is stale.
- Alert evaluation skipped because confidence is low.
- Telegram disabled.
- Telegram delivery failed.
- Earnings event not summarized yet.
- Summary generated with caveats.
- Runtime or migration missing.
- Command failed.

### Safety and Copy Constraints

Avoid:

- Buy signal, sell signal, guaranteed, profit opportunity, hot stock, best stock, AI predicts, recommended buy, this will go up.

Use:

- Rule condition matched, candidate for review, needs review, based on available local data, check freshness and confidence, decision support, alert event, possible issue, post-event summary, caveats.

### Test Plan Proposal

Core tests:

- Create alert rule.
- Evaluate alert rule.
- Skip alert if data is stale.
- Skip alert if confidence is low.
- Create alert event on match.
- No event on no-match.
- Mark false positive.
- Acknowledge and dismiss event.
- Telegram disabled does not fail alert evaluation.
- Telegram delivery failure does not delete local event.
- Create and list earnings event.
- Generate earnings summary with caveats.

UI tests:

- No alert rules empty state.
- No alert events empty state.
- Skipped stale-data state.
- False-positive action visible.
- Telegram disabled state.
- Earnings empty state.
- Earnings summary caveat visible.
- No buy/sell/profit promise copy.
- No raw traceback.

### Risks and Dependencies

- Alert lifecycle depends on V1-S1 freshness, V1-S2 coverage/confidence, and V1-S5 runtime error handling.
- Manual evaluation means alerts are not realtime; UI copy must set that expectation clearly.
- Telegram secret handling must be redacted by default.
- Earnings summaries need enough manual/local input to avoid false confidence.
- Schema must preserve explainability and false-positive feedback before delivery channels are added.

### V1-S6-02 Implementation Notes

- Migration path: `packages/core/schemas/migrations/0007_alerts_earnings.sql`.
- Alert core module: `packages/core/alerts`.
- Implemented rule types: `price_above`, `price_below`, `volume_above`.
- Manual evaluation reads local OHLCV, source freshness, and fundamental confidence.
- Skipped stale/low-confidence evaluations do not create alert events.
- Telegram delivery remains a disabled/placeholder boundary only.
- Earnings workflow remains schema placeholder only.

### V1-S6-03 Implementation Notes

- Alerts route: `apps/web/src/app/alerts`.
- Alerts dashboard: `apps/web/src/components/AlertsDashboard.tsx`.
- Web bridge: `apps/web/src/lib/alerts.ts`.
- UI supports listing rules/events, creating simple threshold rules, manual evaluation, pause/archive, acknowledge/dismiss, and mark false positive.
- Missing migration/schema states use structured runtime errors and recommend `uv run python -m scripts.migrate`.
- Telegram remains disabled placeholder only; earnings workflow remains unimplemented.

### V1-S6-04 Implementation Notes

- Earnings route: `apps/web/src/app/earnings`.
- Earnings dashboard: `apps/web/src/components/EarningsDashboard.tsx`.
- Earnings core module: `packages/core/earnings`.
- Earnings CLI: `scripts.earnings`.
- User can create/list manual earnings events, update notes, archive events, and generate caveated post-event summaries from manual/local input.
- Summary output stores caveats, confidence status, and input snapshot JSON.
- Missing migration/schema states use structured runtime errors and recommend `uv run python -m scripts.migrate`.
- No scraping, Telegram delivery, FastAPI sidecar, background scheduler, or signal/profit language was added.

### V1-S6-05 Implementation Notes

- Telegram config uses env vars: `SAHAMLENS_TELEGRAM_BOT_TOKEN` and `SAHAMLENS_TELEGRAM_CHAT_ID`.
- Telegram status is safe when not configured and never renders token/chat id values.
- Telegram send is explicit/manual through `uv run python -m scripts.alerts --json telegram send --event-id <id>`.
- Local alert events remain the source of truth; delivery attempts are recorded in `alert_delivery_attempts`.
- Delivery statuses: `skipped_not_configured`, `sent`, and `failed`.
- Delivery failure does not mutate, delete, or invalidate local alert events.
- Alerts UI shows optional Telegram state and a `Send to Telegram` action only when configured.
- Tests mock Telegram network calls; no real Telegram send is performed by automated tests.
- No FastAPI, background scheduler, broker integration, scraping, or signal/profit language was added.

### V1-S6 Final Closeout

- V1-S6 status: completed on `v1/s6-alert-lifecycle`.
- Implemented local alert lifecycle, manual alert evaluation, alert event review, false-positive tracking, optional manual Telegram delivery, manual-first earnings events, and caveated earnings summaries.
- CLI surfaces: `scripts.alerts` and `scripts.earnings`.
- UI surfaces: `/alerts` and `/earnings`.
- Migration: `0007_alerts_earnings.sql`.
- Runtime readiness includes alert and earnings tables and recommends `uv run python -m scripts.migrate` when local DB is stale.
- Telegram uses env-based secrets, shows only configured/not-configured booleans, and records redacted delivery attempts.
- Automated tests mock Telegram network calls and do not send real messages.
- Local DB mutation policy remains explicit: `status` is read-only; developers must run `scripts.migrate` or `scripts.runtime bootstrap` intentionally.
- Constraints preserved: no FastAPI, no scheduler/background service, no broker integration, no scraping, no auto-trading, no realtime/intraday alerting, and no signal/profit language.

## First Safe PR Order

1. Provider health ADR and freshness terminology.
2. Provider health schema/model.
3. Data Quality Dashboard shell with static empty states.
4. Provider health refresh CLI smoke path.
5. Freshness status rendering and stale/fail UI states.
6. Coverage model ADR and enums.
7. Fundamental snapshot schema and completeness labels.
8. Screener semantics ADR.
9. Runtime and UX state regression tests.
10. V1-S6 alert lifecycle, Telegram optional, and earnings manual-first scope lock.
11. `0007_alerts_earnings.sql` migration and repository tests.

## Sprint Gates

Each sprint is done only when:

- Tests for touched modules pass.
- UI states for fresh, stale, failed, partial, and unknown are represented where relevant.
- Dogfooding ticket is completed with notes.
- Docs are updated only in canonical files.
- No private data is committed.
- No anti-scope feature is introduced.

## Risk Burn-Down Order

1. Data trust.
2. Data coverage.
3. Fundamental quality.
4. Screener quality.
5. UX polish.
6. Alert quality.
7. Earnings workflow.

## Execution Rules

- Start V1-S6 from the scope lock and ADR/data contract before creating schema.
- Keep PRs small and vertical.
- Do not implement optional Telegram before alert lifecycle works locally in V1-S6.
- Do not implement screener before Data Quality and coverage gates exist.
- Do not use AI output as a trading signal.
- Do not add new providers without source visibility and caveats.

## Starting Point

Recommended next command: `Release readiness / PR review`.
