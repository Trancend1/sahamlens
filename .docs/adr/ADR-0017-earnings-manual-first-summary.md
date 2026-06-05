# ADR-0017: Earnings Manual-First Summary

Status: Accepted
Date: 2026-06-05

## Context

Earnings context is useful for daily review, but reliable automated IDX filing or earnings scraping is not in V1 scope. V1 should support a lightweight workflow that helps the user document and summarize earnings events without implying prediction or recommendation.

## Decision

V1-S6 earnings workflow is manual-first.

Rules:

- User can manually register an earnings event.
- User can attach notes, source reference, or summary input.
- Summary must be based on local/manual data available in SahamLens.
- Summary output must include caveats and confidence.
- Source type and source reference must be visible.
- No unreliable automated scraping is introduced in V1-S6.
- No output may judge a stock as good/bad, buy/sell, or likely to move.
- The workflow supports post-event review, not prediction.

## Consequences

Positive:

- Earnings utility can ship without brittle scraping.
- User remains in control of source selection and context.
- Summaries stay explainable and caveated.
- V1 avoids turning earnings into a financial terminal.

Trade-offs:

- Manual entry is slower than automation.
- Coverage depends on user input or validated local data.
- Automated discovery can be revisited only after source reliability is proven.

## Non-Goals

- Automated IDX crawling.
- Full article or filing republication.
- Earnings prediction.
- Buy/sell recommendation.
- Public recommendations or signal content.
- Licensed realtime market data integration.
