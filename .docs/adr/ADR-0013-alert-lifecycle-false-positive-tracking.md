# ADR-0013: Alert Lifecycle and False-Positive Tracking

Status: Accepted
Date: 2026-05-31
Updated: 2026-06-05

## Context

Alerts can become noisy and erode trust. V1 allows local alert rules only if alert events are explainable, lifecycle states are explicit, data quality gates are respected, and false-positive feedback is tracked.

## Decision

V1-S6 alerts are local-first, manually evaluated, reviewable, and confidence-gated decision-support events.

Rules:

- Alert definitions are stored locally.
- Alert evaluations are manually invoked through CLI-backed local runtime.
- Alert events must exist locally before optional notification delivery.
- Freshness and confidence gates must run before creating actionable alert events.
- User review and false-positive feedback are part of the core lifecycle.
- No background service, daemon, or always-on scheduler is introduced in V1-S6.

Allowed alert types:

- Price threshold.
- Moving-average crossover.
- Volume anomaly.
- Freshness degradation.
- Provider failure.

Rejected alert types:

- Predictive alerts.
- AI buy/sell alerts.
- Forecasting alerts.
- Broker/order execution alerts.
- Public recommendation alerts.

## Lifecycle

Alert definition states:

- `active`.
- `paused`.
- `archived`.

Alert event states:

- `new`.
- `acknowledged`.
- `dismissed`.
- `marked_false_positive`.
- `resolved`.

Alert evaluation states:

- `success`.
- `skipped_stale_data`.
- `skipped_low_confidence`.
- `failed_provider`.
- `failed_runtime`.
- `no_match`.

Events must store the rule, evaluation reference, input data reference, source/freshness state, confidence state, created timestamp, explanation, caveats, and review status.

## False Positive Definition

An alert event is a false positive when the user marks that it was not useful or should not have fired under the intended rule.

False positive examples:

- Trigger caused by stale, failed, or partial data.
- Trigger caused by known corporate action not modeled by the rule.
- Trigger technically matched but was not actionable or useful for the user's workflow.
- Trigger repeated too often without new information.

False positive tracking is quality feedback, not model training and not predictive labeling.

## Quality Expectations

- Alert events must be explainable.
- Alert detail must show rule, source, timestamp, freshness state, and caveats.
- Alert quality should track false-positive count/rate.
- V1 dogfooding target is below 30 percent false-positive rate after enough usage.
- Notification channels such as Telegram are optional and must not bypass lifecycle tracking.
- Missing optional delivery config is a disabled state, not an alert failure.

## Data Quality Dependency

- Price/technical alerts require fresh or delayed acceptable OHLCV.
- Provider/freshness alerts may trigger when data is stale, failed, partial, or unknown.
- Fundamental alerts are not part of V1 unless explicitly scoped later.
- Alerts must respect ticker coverage tier restrictions.
- Low-confidence or stale data should produce skipped evaluations unless the rule is explicitly a provider/freshness degradation rule.

## Schema Implications

Schema should support:

- Alert rule definition.
- Rule state.
- Alert evaluation record.
- Evaluation state.
- Alert event record.
- Event state.
- Triggered timestamp.
- Acknowledged/dismissed/false-positive/resolved timestamp.
- False-positive flag and feedback note.
- Source/freshness snapshot.
- Confidence snapshot.
- Quality aggregate or computable metrics.

## Consequences

Positive:

- Keeps alerts trustworthy and auditable.
- Prevents notification-first implementation from creating noise.
- Gives V1 a measurable alert-quality target.

Trade-offs:

- Alerts require feedback UI and persistence before optional Telegram delivery.
- Some useful ideas are rejected until they can be explained without predictive language.

## Follow-Up

Telegram notifications may be added only as optional delivery after local alert lifecycle and feedback persistence work. See [ADR-0016](ADR-0016-telegram-optional-delivery.md).
