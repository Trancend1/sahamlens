# ADR-0016: Telegram Optional Alert Delivery

Status: Accepted
Date: 2026-06-05

## Context

Telegram can make local alerts more useful, but notification delivery must not become the source of truth or add deployment complexity. SahamLens V1 remains local-first, single-user, CLI-backed, and public-repo-safe.

## Decision

Telegram is optional delivery, not the alert source of truth.

Rules:

- Alert events must exist locally before delivery is attempted.
- Telegram config is optional and disabled by default.
- Missing Telegram config produces a clear disabled state, not an error.
- Config uses `SAHAMLENS_TELEGRAM_BOT_TOKEN` and `SAHAMLENS_TELEGRAM_CHAT_ID`.
- Status output may expose only boolean presence fields such as `bot_token_configured`
  and `chat_id_configured`.
- Alert review, acknowledgement, dismissal, and false-positive tracking remain local.
- Telegram delivery may fail without invalidating the local alert event.
- Bot token and chat id must never be rendered in UI or logged in plaintext.
- Delivery errors must store redacted details only.
- Telegram send is explicit/manual in V1-S6.
- V1-S6 must not introduce a long-running service, daemon, scheduler, or FastAPI sidecar for Telegram.

## Consequences

Positive:

- Alerts remain usable without Telegram.
- Secrets stay outside user-facing output.
- Notification failures do not destroy local alert history.
- V1 keeps the local runtime simple.

Trade-offs:

- Telegram delivery is best-effort in V1-S6.
- Alerts are not realtime because evaluation is manually invoked.
- Background delivery can be reconsidered only after local alert lifecycle quality is proven.
- Automated tests must mock Telegram network calls and must not send real messages.

## Non-Goals

- Always-on notification service.
- Cloud push notification provider.
- Multi-user notification routing.
- Broker/order notification integration.
- Signal-selling or public recommendation delivery.
