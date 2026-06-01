# ADR-0014: Screener Semantics

Status: Accepted
Date: 2026-06-01

## Context

The V1 screener depends on Data Quality, ticker coverage, lifecycle status, freshness,
and fundamental completeness/confidence. Without shared screener semantics, filters can
quietly become recommendations, hide missing data, or include unsupported tickers.

## Decision

V1 screener results are transparent filter results, not trading signals.

Allowed screener language:

- Matched filter.
- Did not match filter.
- Excluded.
- Ineligible.
- Missing data.
- Stale data.
- Requires caveat.

Rejected screener language:

- Buy.
- Sell.
- Hold.
- Strong buy.
- Safe.
- Guaranteed.
- Predicted winner.
- Best pick.
- Recommendation.

## Rule Semantics

Every screener rule must declare:

- Rule identifier.
- Rule name.
- Rule description.
- Required fields.
- Required source types.
- Minimum coverage tier.
- Allowed freshness states.
- Minimum fundamental completeness when fundamentals are required.
- Minimum confidence level when confidence is required.
- Transparent conditions.

Rules must be explicit and inspectable. V1 must not introduce a strategy DSL.

## Result Semantics

Every screener run must produce explainable results:

- Included tickers matched all required conditions.
- Excluded tickers must include one or more exclusion reasons.
- Missing fields must be listed.
- Stale, failed, partial, or unknown freshness must be visible.
- Tier C tickers are excluded from screener results.
- Suspended, delisted, renamed-without-alias, and unknown lifecycle states are excluded
  unless a later ADR explicitly defines an override.
- Sparse or missing fundamentals exclude rules that require fundamentals.

## Data Quality Gates

Screener evaluation must respect:

- Provider health.
- OHLCV freshness.
- Ticker lifecycle status.
- Coverage tier.
- Source coverage.
- Fundamental completeness.
- Fundamental confidence.

Fresh and delayed data may be used with caveats. Stale, failed, unknown, or missing
required data must restrict or exclude the affected rule evaluation.

## AI Boundary

AI may explain why a ticker matched or did not match a transparent rule. AI must not
turn screener output into buy/sell/hold language, rankings as recommendations, or
price forecasts.

Screener explanations must remain evidence-led and include caveats when data is
partial, stale, sparse, or unofficial.

## Schema Implications

Schema should support:

- Screener rule definition.
- Rule condition records.
- Required field metadata.
- Freshness and confidence gates.
- Screener run metadata.
- Screener result records.
- Inclusion/exclusion status.
- Explanation and caveat text.
- Missing field list.
- Data snapshot references or captured gate values.

## Consequences

Positive:

- Keeps screener output explainable and safe.
- Prevents false confidence from incomplete data.
- Gives UI, CLI, and AI one shared vocabulary for filter results.
- Makes dogfooding quality measurable by reviewing inclusion and exclusion reasons.

Trade-offs:

- Some potentially useful tickers will be excluded until data quality improves.
- Rule definitions require more metadata than a simple filter expression.
- V1 cannot support arbitrary strategy DSL behavior.

## Follow-Up

V1-S3 schema, evaluator, CLI, and UI must consume this ADR rather than creating
parallel rule terminology.
