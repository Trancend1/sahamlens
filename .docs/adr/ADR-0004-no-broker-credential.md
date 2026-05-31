# ADR-0004: No Broker Credentials or Broker Integration

Status: Accepted
Date: 2026-05-31

## Context

Broker integration would introduce credential risk, legal/compliance concerns, order-execution liability, and maintenance burden. SahamLens is decision-support only.

## Decision

V1 will not store or use broker credentials, cookies, sessions, account APIs, or automated order flows.

Rejected:

- Broker login.
- Broker cookie/session reuse.
- Account sync through authenticated broker pages.
- Order placement or staged order automation.
- Scraping private broker pages.

Allowed:

- Local manual CSV import controlled by the user.
- User-written notes about trades.
- Risk sizing as calculation support, not order execution.

## Consequences

Positive:

- Lower privacy and liability risk.
- Keeps repo public-safe.
- Preserves decision-support boundary.

Trade-offs:

- Portfolio freshness may require manual import.
- No automated reconciliation with broker records.

## Follow-Up

Any broker integration requires a new ADR, security review, PRD update, and explicit user approval.
