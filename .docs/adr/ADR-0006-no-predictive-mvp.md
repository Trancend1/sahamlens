# ADR-0006: No Predictive AI or Buy/Sell Signals

Status: Accepted
Date: 2026-05-31

## Context

SahamLens is a decision-support tool. Predictive claims and buy/sell instructions create false confidence and move the product toward signal selling.

## Decision

AI and alert features must not produce predictive trading signals.

Rejected:

- AI buy/sell/hold recommendations.
- Forecasting alerts.
- Exact future price targets as fact.
- "Guaranteed", "safe", or "strong buy" language.
- Public recommendation or signal-selling output.

Allowed:

- Evidence summaries.
- Caveats.
- Rule-match explanations.
- User-plan critique.
- Journal reflection.

## Consequences

Positive:

- Stronger user trust.
- Clearer legal and safety boundary.
- Less temptation to overfit or overclaim.

Trade-offs:

- Some "assistant" requests must be refused or reframed.
- Copy and validation need continuous care.

## Follow-Up

Any predictive analytics feature belongs outside V1 and requires separate ADR and PRD review.
