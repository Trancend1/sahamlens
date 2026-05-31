# SahamLens Execution Blueprint

## Status

V1 planning is frozen and ready for implementation.

Current phase: Phase V1 - Better Decision Support.
Current sprint: V1-S1 - Provider Health + Data Quality Foundation.

Implementation must follow the critical path:

Data Quality -> Coverage/Fundamentals -> Screener -> Alerts

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

Can be written during the related sprint:

- Screener semantics.
- Earnings manual-first hierarchy.
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
| V1-S5 | Alerts + Telegram Optional + Earnings Summary | Add local alert lifecycle and manual-first earnings workflow. | User can receive/review local alerts, track false positives, and summarize earnings events. |

## Dependency Matrix

| Sprint | Blocked by | Enables | Parallelizable |
|---|---|---|---|
| V1-S1 | None | V1-S2, V1-S3, V1-S5 | UI shell, provider registry, docs cleanup |
| V1-S2 | V1-S1 | V1-S3, V1-S5 | Fundamental UI and lifecycle schema can be split |
| V1-S3 | V1-S1, V1-S2 | V1-S5 | Screener UI and rule fixtures |
| V1-S4 | Existing journal baseline | V1-S5 context | Can run parallel after V1-S1 |
| V1-S5 | V1-S1, V1-S2, V1-S3 | V1 exit | Telegram optional and earnings manual path can be split |

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

- ADR-S5-01: Alert lifecycle and false-positive tracking ADR.
- ADR-S5-02: Earnings manual-first hierarchy ADR or RFC-only confirmation.
- SCHEMA-S5-01: Alert rules, events, feedback.
- SCHEMA-S5-02: Earnings event metadata.
- CORE-S5-01: Alert evaluator.
- CORE-S5-02: Alert feedback and quality tracking.
- CORE-S5-03: Earnings summary manual workflow.
- CLI-S5-01: Evaluate alerts.
- CLI-S5-02: Record alert feedback.
- CLI-S5-03: Create earnings summary.
- UI-S5-01: Alerts page.
- UI-S5-02: Earnings Summary section.
- OPTIONAL-S5-01: Telegram notification sender.
- TEST-S5-01: Alert lifecycle and false-positive tests.
- DOGFOOD-S5: Alert and earnings review.

## First Safe PR Order

1. Provider health ADR and freshness terminology.
2. Provider health schema/model.
3. Data Quality Dashboard shell with static empty states.
4. Provider health refresh CLI smoke path.
5. Freshness status rendering and stale/fail UI states.
6. Coverage model ADR and enums.
7. Fundamental snapshot schema and completeness labels.
8. Screener semantics ADR.
9. Alert lifecycle ADR.
10. Alert feedback model.

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
5. Alert quality.
6. Earnings workflow.
7. UX polish.

## Execution Rules

- Start with V1-S1.
- Keep PRs small and vertical.
- Do not implement optional Telegram before alert lifecycle works locally.
- Do not implement screener before Data Quality and coverage gates exist.
- Do not use AI output as a trading signal.
- Do not add new providers without source visibility and caveats.

## Starting Point

Recommended next step: write or confirm the five mandatory ADRs, then open the first V1-S1 PR for provider health and freshness terminology.
