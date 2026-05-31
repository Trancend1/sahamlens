# ADR-0010: OHLCV Freshness Contract

Status: Accepted
Date: 2026-05-31

## Context

SahamLens uses yfinance as the V1 baseline for EOD OHLCV. The product must not imply realtime market data. Market-hours refresh can be useful only if clearly labeled as delayed or indicative.

## Decision

V1 OHLCV is EOD-first.

Every OHLCV-derived surface must show source and freshness. Realtime or tick-data promises are rejected for V1.

## Freshness States

- Fresh: latest available EOD data is within the accepted daily window for the market calendar.
- Delayed: data was refreshed during market hours or expected provider lag; usable only with a caveat.
- Stale: data is older than the accepted window.
- Failed: latest fetch failed; last successful timestamp must be shown if available.
- Partial: fetch succeeded for only part of the requested coverage.
- Unknown: source or timestamp cannot be trusted.

## Policy

- EOD OHLCV is accepted as the default baseline.
- Market-hours refresh is allowed only as delayed/indicative.
- Intraday snapshot is deferred.
- Realtime/tick data is rejected.
- yfinance is allowed as an unofficial provider with visible caveats.

## Downstream Behavior

- Dashboard must show freshness state and source.
- Screener must restrict rules affected by stale, failed, partial, or unknown OHLCV.
- Alerts must not emit new price/technical triggers from stale, failed, or unknown OHLCV.
- AI summaries must mention delayed, stale, failed, partial, or unknown OHLCV before interpretation.
- Trade-plan workflow must keep the user responsible for final verification.

## Consequences

Positive:

- Prevents false realtime expectations.
- Gives one shared freshness vocabulary for V1.
- Keeps V1 low-maintenance and local-first.

Trade-offs:

- Some market-hours user expectations must be handled through caveats instead of live claims.
- UI needs explicit disabled/read-only states for stale and failed data.

## Follow-Up

Ticker coverage and alert lifecycle ADRs must use these freshness states rather than inventing new status names.
