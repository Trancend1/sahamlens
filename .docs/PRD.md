# SahamLens PRD

## Product Identity

SahamLens is a local-first personal trading companion for one retail IDX trader. It helps the owner inspect market data, fundamentals, news metadata, journal history, and simple rules before making their own decision.

SahamLens does not decide, recommend, execute, or sell signals. AI may explain and critique, but the user remains the decision maker.

## Principles

- Local-first: private data stays on the user's machine by default.
- Single-user: no teams, tenants, billing, roles, or public distribution workflows.
- Decision-support: show evidence, caveats, freshness, and confidence.
- Low maintenance: prefer simple files, CLI jobs, and public providers that can fail gracefully.
- Explainable: every summary must show source and limitations.
- No predictive AI: no future price forecast as fact, no buy/sell instruction.

## V1 Goal

V1 turns the current learning dashboard into a better decision-support layer:

- The user can trust whether data is fresh enough to use.
- The user can inspect lightweight fundamentals with confidence labels.
- The user can filter candidates through transparent screener rules.
- The user can track local alert events and false positives.
- The user can review weekly behavior and simple strategy-rule violations.
- The user can summarize earnings events manually first, with source metadata.

## Primary User Workflow

1. Open Data Quality Dashboard.
2. Confirm provider health, freshness, coverage, and source issues.
3. Review watchlist and ticker coverage.
4. Inspect Fundamental Snapshot for selected tickers.
5. Run screener rules with visible caveats.
6. Review alerts and mark false positives.
7. Add journal notes and weekly review.
8. Use AI only to explain evidence and caveats.

## V1 Core Scope

| Feature | Product decision |
|---|---|
| Data Quality Dashboard | Core. Prerequisite for screener and alerts. |
| Provider Health | Core inside Data Quality Dashboard. |
| Ticker Lifecycle and Coverage | Core. Required for eligibility decisions. |
| Fundamental Snapshot | Core. Lightweight snapshot, not a financial terminal. |
| Fundamental Completeness and Confidence | Core. Prevents false confidence. |
| Screener | Core. Transparent filters, no signal language. |
| Local Alert Rules and Events | Core. Local-only, explainable, with feedback tracking. |
| Weekly Journal Review | Core. Behavior review, not performance marketing. |
| Simple Strategy Rules | Core. Named checks only, no custom DSL. |
| Earnings Summary | Core manual-first workflow with source metadata. |

## V1 Optional Scope

- Telegram notifications for local alert delivery.
- Market-hours delayed or indicative refresh, clearly labeled.
- Extra validated RSS feeds after Detik Finance, CNBC Indonesia, and Kontan.
- Provider-ready LLM direction without adding multi-provider UX complexity.
- RSS-backed earnings event discovery as helper, not authority.

## Deferred or Experimental

- Intraday snapshot.
- Backtesting-lite.
- Performance analytics beyond weekly review.
- Automated IDX filing/parser pipeline.
- Social sentiment or Stockbit/Twitter streams.

These are not part of V1 execution unless a later phase unlocks them.

## Rejected Scope

- Realtime or tick-data promise.
- AI buy/sell alerts or predictive alerts.
- Broker login, cookies, sessions, account sync, or order placement.
- Automated IDX crawling for V1.
- Public recommendations, signal selling, SaaS, or multi-user expansion.
- Strategy DSL for V1.
- Full news article storage or republication.

## Success Metrics

- Data trust: user can see fresh, stale, failed, partial, and unknown data states.
- Coverage clarity: every ticker has clear support tier and missing-data explanation.
- Fundamental safety: incomplete fundamentals are labeled and constrained in screener/AI.
- Screener utility: filters produce explainable candidates without recommendation language.
- Alert quality: false positives are tracked; target false-positive rate below 30 percent after dogfooding.
- Daily utility: owner can use V1 in a 15-30 minute personal review flow.

## Exit Criteria

V1 exits when:

- Data Quality Dashboard is usable before screener and alerts.
- Fundamental Snapshot and confidence labels are visible for watchlist tickers.
- Screener results are explainable and freshness-aware.
- Alerts have lifecycle states and false-positive feedback.
- Weekly review and simple strategy rules support owner reflection.
- Earnings summary has manual fallback and source metadata.
- Governance docs and ADRs match implementation.

## Change Control

Planning is frozen. Scope changes require:

1. A concrete blocker or material new constraint.
2. Update to this PRD if product scope changes.
3. ADR if architecture, data trust, AI safety, or schema contracts change.
4. Backlog update in [EXECUTION_BLUEPRINT.md](EXECUTION_BLUEPRINT.md).
