# Design System

## Design Goal

SahamLens should feel like a calm personal trading cockpit: dense enough for daily review, restrained enough to avoid false urgency.

## Principles

- Evidence first: show source, timestamp, freshness, and caveat near the data.
- No signal theater: avoid aggressive colors, hype copy, and buy/sell framing.
- Compact workflows: daily review should fit a 15-30 minute ritual.
- Clear disabled states: unavailable actions must explain why.
- Local-first trust: privacy and data-quality status should be visible.

## Core Surfaces

- Data Quality Dashboard.
- Watchlist and ticker detail.
- Fundamental Snapshot card.
- Screener page.
- Alerts page.
- Weekly Journal Review page.
- Strategy Rules page.
- Earnings Summary section.

## Status Vocabulary

Freshness states:

- Fresh.
- Delayed.
- Stale.
- Failed.
- Partial.
- Unknown.

Coverage tiers:

- Tier A: Full Support.
- Tier B: Partial Support.
- Tier C: Minimal Support.

Fundamental completeness:

- Complete.
- Partial.
- Sparse.
- Missing.

## Visual Treatment

- Fresh: normal state.
- Delayed/Partial: caution state, still readable.
- Stale/Failed/Unknown: warning state with restricted actions.
- Missing data: empty state with reason and next step.
- AI output: evidence and caveats must be scannable before interpretation.

Avoid decorative UI that competes with data. No public-marketing hero sections inside the product dashboard.

## Copy Rules

Use:

- "Rule matched".
- "Needs verification".
- "Data stale".
- "Excluded because".
- "Not enough data".

Avoid:

- "Buy signal".
- "Safe".
- "Guaranteed".
- "Strong buy".
- "Best stock".

## Component Rules

- Use cards for repeated ticker/results items, not for every section.
- Keep tables scannable and sortable where useful.
- Use badges for status, not long paragraphs.
- Put explanations close to disabled controls.
- Prefer existing shadcn/ui components and project patterns.
