# ADR-0009: Provider Health as V1 Prerequisite

Status: Accepted
Date: 2026-05-31

## Context

V1 depends on public and unofficial providers, especially yfinance for EOD OHLCV and validated RSS feeds for news metadata. Screener and alert features can create false confidence if provider failures, stale data, or partial coverage are hidden.

## Decision

Provider Health is an architecture prerequisite for V1.

Screener, alerts, fundamental snapshots, and AI summaries must depend on visible provider health and freshness state before presenting decision-support output.

The Data Quality Dashboard is the first V1 foundation slice and must expose provider health before dependent V1 features are treated as usable.

## Minimum Provider Health Fields

- Provider name.
- Provider trust tier.
- Source type.
- Last successful fetch timestamp.
- Last failed fetch timestamp.
- Last failure reason.
- Consecutive failure count.
- Freshness state.
- Coverage count where applicable.
- Updated timestamp.

## Behavior

- Fresh providers can support normal downstream flows.
- Delayed providers can support flows only with a visible caveat.
- Stale, failed, partial, or unknown providers restrict dependent screener and alert behavior.
- Last successful data may remain visible only with timestamp and caveat.
- Provider failure can trigger provider/freshness alerts, but not trading-signal alerts.

## Consequences

Positive:

- Data trust is visible before decision-support features expand.
- Screener and alerts get a shared safety gate.
- Provider issues become observable during daily dogfooding.

Trade-offs:

- V1-S1 must build foundation work before feature-visible screener/alert utility.
- Provider models and UI states need care before adding more providers.

## Implementation Notes

Expected first surfaces:

- Provider health schema/model.
- Provider health collector.
- Data quality aggregation.
- Refresh provider health CLI.
- Data Quality Dashboard shell.
- Freshness/provider health tests.

## Follow-Up

Ticker lifecycle, fundamental confidence, screener semantics, and alert lifecycle ADRs must build on this provider-health prerequisite.
