# ADR-0012: Fundamental Completeness and Confidence

Status: Accepted
Date: 2026-05-31

## Context

V1 fundamentals are lightweight snapshots from public or manually verified sources. They are not a financial terminal. Missing, stale, or sparse fundamentals can create false confidence if shown like complete data.

## Decision

V1 will classify every fundamental snapshot with a completeness state and confidence level.

Completeness states:

- Complete.
- Partial.
- Sparse.
- Missing.

Confidence must be derived from:

- Coverage score.
- Freshness score.
- Provider trust score.
- Completeness score.

The model is decision-support metadata, not a predictive score.

## Completeness Behavior

Complete:

- Required fields for the snapshot are present.
- Source and timestamp are known.
- Freshness is acceptable.
- Eligible for fundamental screener rules.
- AI may explain normally with caveats.

Partial:

- Important fields exist, but some fields are missing.
- Eligible only for rules that do not require missing fields.
- UI must show missing fields.
- AI must mention missing fields.

Sparse:

- Few fields are available or source quality is weak.
- Usually excluded from fundamental screener rules.
- UI must show low confidence.
- AI must explain limitations before interpretation.

Missing:

- No usable snapshot exists.
- Not eligible for fundamental screener rules.
- UI must show empty/missing state.
- AI must not infer fundamentals.

## Freshness and Trust Impact

- Stale fundamentals lower confidence even if fields are present.
- Failed or unknown sources prevent high confidence.
- Tier 1 official/manual-verified sources can raise trust.
- Tier 3 unofficial sources require visible caveats.
- Conflicting sources should lower confidence or require manual review.

## Schema Implications

Schema should support:

- Symbol.
- Snapshot period/date.
- Source and source type.
- Fetched/imported timestamp.
- Available fields.
- Missing fields.
- Completeness state.
- Confidence label or score.
- Caveat/reason text.

## Downstream Impact

- Fundamental Snapshot card must show completeness and confidence.
- Screener must be field-aware and avoid rules with missing inputs.
- Alerts must not trigger fundamental events from stale, failed, sparse, or missing data unless the alert is specifically about data quality.
- AI summaries must include completeness and confidence caveats.

## Consequences

Positive:

- Reduces false confidence from incomplete fundamentals.
- Gives screener and AI a shared safety gate.
- Supports manual-first verification without pretending all sources are equal.

Trade-offs:

- Some ticker fundamentals will look intentionally limited.
- More metadata is required than a simple key-value snapshot.

## Follow-Up

The screener semantics ADR should define how rules declare required fields and how missing fields affect results.
