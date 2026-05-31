# SahamLens Data Sources

## Data Strategy

V1 uses public, low-maintenance sources with visible freshness and caveats. yfinance remains the baseline for EOD OHLCV. Fundamentals are lightweight snapshots. News is metadata-only through validated RSS feeds.

Every user-facing data point that affects decisions must show source and freshness.

## Provider Trust Tiers

| Tier | Description | Usage |
|---|---|---|
| Tier 1 | Official sources | Highest trust, preferred for formal filings and exchange facts. |
| Tier 2 | Reputable public providers | Accepted for V1 when source and freshness are visible. |
| Tier 3 | Unofficial providers | Allowed only with caveats and fallback behavior. |
| Tier 4 | Experimental providers | Not used for core V1 decisions. |

Current mapping:

- IDX official pages/filings: Tier 1, manual/reference use in V1.
- yfinance: Tier 3, accepted baseline for EOD OHLCV with caveats.
- Detik Finance RSS: Tier 2, accepted metadata-only news.
- CNBC Indonesia RSS: Tier 2, accepted metadata-only news.
- Kontan RSS: Tier 2, accepted metadata-only news.
- Telegram Bot API: delivery channel only, not market data.
- Stockbit, Twitter/X, broker apps, scraped authenticated pages: rejected for V1 core.

## OHLCV Policy

Accepted:

- EOD OHLCV is the V1 baseline.
- yfinance may be used for local decision-support with visible caveats.
- Last successful fetch timestamp must be stored.

Accepted with caveat:

- Market-hours refresh may be delayed/indicative and must be labeled as such.

Deferred:

- Intraday snapshot.

Rejected:

- Realtime/tick-data promise.
- Licensed realtime market data unless a later phase adds explicit legal/contract support.

## Fundamental Policy

Accepted:

- V1 fundamentals are lightweight snapshots.
- Store source, fetched/imported timestamp, available fields, missing fields, completeness, and confidence.
- Incomplete data must be visible in UI and AI summaries.

Accepted with caveat:

- Public-provider fundamentals may be stale or sparse.
- Manual verification is acceptable for important decisions.

Rejected:

- Full financial terminal scope.
- Automated IDX filing/parser pipeline for V1.

## News Policy

Accepted:

- Use validated RSS feeds for headline, link, source, published timestamp, and summary metadata.
- Deduplicate and show source.

Accepted with caveat:

- Additional RSS feeds can be added only after validation.

Rejected:

- Full article storage.
- Article republication.
- Paywall bypass.
- Social stream ingestion for V1.

## Ticker Universe Policy

Ticker lifecycle statuses:

- Active.
- Suspended.
- Delisted.
- Renamed.
- Unknown.

Rules:

- Delisted tickers remain historical but are not screener-eligible.
- Suspended tickers show warnings and are alert-limited.
- Renamed tickers require alias mapping before being treated as fully supported.
- Unknown tickers are minimal support until coverage is verified.

## Coverage Tiers

| Tier | Meaning | Screener | Alerts | AI explanation |
|---|---|---|---|---|
| Tier A | OHLCV available, lifecycle known, fundamentals at least partial, source health visible | Eligible | Eligible | Eligible with caveats |
| Tier B | OHLCV available but fundamentals sparse or lifecycle uncertain | Limited | Price/freshness alerts only | Allowed with strong caveats |
| Tier C | Minimal or unreliable data | Not eligible | Freshness/provider alerts only | Explain missing data only |

UI behavior:

- Never hide missing data.
- Disable or mark read-only actions when required data is stale, failed, or missing.
- Show why a ticker is excluded from screener/alert eligibility.

## Fundamental Completeness

| Status | Meaning | Confidence | Screener behavior | AI behavior |
|---|---|---|---|---|
| Complete | Required fields present and fresh enough | High | Eligible | Explain normally with caveats |
| Partial | Important fields present but some missing | Medium | Eligible only for rules not requiring missing fields | Mention missing fields |
| Sparse | Few fields available | Low | Usually excluded from fundamental rules | Explain limitations first |
| Missing | No usable fundamental snapshot | None | Not eligible | Do not infer fundamentals |

## Provider Health Metrics

Minimum V1 metrics:

- Last successful fetch.
- Last failed fetch.
- Error count.
- Failure reason.
- Freshness state.
- Provider trust tier.
- Ticker/source coverage count.

Provider failure behavior:

- Show failure in Data Quality Dashboard.
- Keep last successful data visible with timestamp.
- Restrict dependent screener/alert flows when freshness is stale or failed.

## Freshness UX Contract

| State | Dashboard | Screener | Alerts | AI summaries |
|---|---|---|---|---|
| Fresh | Normal | Enabled | Enabled | Normal caveats |
| Delayed | Labeled | Enabled with caveat | Enabled if rule allows | Mention delay |
| Stale | Warning | Restricted | No new price/fundamental triggers | Explain stale state |
| Failed | Error | Disabled for affected source | Provider/freshness alerts only | Explain failure |
| Partial | Warning | Rule-specific eligibility | Rule-specific eligibility | Mention missing data |
| Unknown | Warning | Disabled | Disabled except provider checks | Do not infer |

## Rejected Data Practices

- Broker login, cookies, sessions, or scraping authenticated pages.
- Automated IDX crawling in V1.
- Realtime/tick-data claims.
- Full article archival.
- Selling or publishing recommendations derived from public data.
