# ADR-0011: Ticker Lifecycle and Coverage Model

Status: Accepted
Date: 2026-05-31

## Context

V1 features depend on knowing whether a ticker is active, supported, stale, suspended, delisted, renamed, or only partially covered. Without a shared lifecycle and coverage model, screener, alerts, and AI summaries can treat weak data as fully usable.

## Decision

V1 will use a shared ticker lifecycle and coverage model before screener and alert eligibility.

Ticker lifecycle status:

- Active.
- Suspended.
- Delisted.
- Renamed.
- Unknown.

Coverage tier:

- Tier A: Full Support.
- Tier B: Partial Support.
- Tier C: Minimal Support.

Coverage tier must be derived from OHLCV availability, lifecycle confidence, provider health, fundamental availability, and source visibility.

## Tier Behavior

Tier A:

- OHLCV is available and fresh enough.
- Lifecycle status is known.
- Provider health is visible.
- Fundamentals are at least partial when required by the feature.
- Eligible for screener and alerts, with normal caveats.
- Eligible for AI explanation.

Tier B:

- OHLCV is available, but fundamentals are sparse, lifecycle is uncertain, or provider coverage is incomplete.
- Eligible only for screener rules that do not depend on missing fields.
- Eligible for price/freshness alerts only.
- AI explanations must emphasize limitations.

Tier C:

- Minimal, missing, failed, or unreliable data.
- Not eligible for screener.
- Eligible only for provider/freshness alerts.
- AI may explain missing data but must not infer ticker quality.

## Lifecycle Behavior

- Active tickers may be Tier A, B, or C depending on coverage.
- Suspended tickers must show warning state and restrict alerts to provider/freshness checks unless manually overridden in a later phase.
- Delisted tickers remain historical but are not screener-eligible.
- Renamed tickers require alias mapping before full support.
- Unknown tickers default to Tier C until verified.

## Schema Implications

Schema should support:

- Symbol.
- Lifecycle status.
- Coverage tier.
- Source/provider references.
- Last verified timestamp.
- Rename/alias metadata where known.
- Missing-data reason.
- Eligibility flags or computed eligibility reason.

## Downstream Impact

- Data Quality Dashboard must surface tier counts and unsupported tickers.
- Fundamental Snapshot must show coverage and missing fields.
- Screener must explain inclusion/exclusion.
- Alerts must respect tier restrictions.
- AI summaries must mention lifecycle and coverage caveats before interpretation.

## Consequences

Positive:

- Prevents unsupported tickers from silently entering decision flows.
- Gives one eligibility vocabulary across V1.
- Makes delisted/suspended/renamed handling explicit.

Trade-offs:

- Requires a coverage refresh path before screener feels complete.
- Some tickers will be intentionally excluded until source quality improves.

## Follow-Up

Fundamental confidence and alert lifecycle decisions must consume this model rather than creating parallel eligibility rules.
