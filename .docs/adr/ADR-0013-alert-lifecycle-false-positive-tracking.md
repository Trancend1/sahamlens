# ADR-0013: Alert Lifecycle and False-Positive Tracking

Status: Accepted
Date: 2026-05-31

## Context

Alerts can become noisy and erode trust. V1 allows local alert rules only if alert events are explainable, lifecycle states are explicit, and false-positive feedback is tracked.

## Decision

V1 alerts will be local decision-support events with an explicit lifecycle and false-positive feedback.

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

Alert rule states:

- Active.
- Paused.
- Archived.

Alert event states:

- Triggered.
- Acknowledged.
- Dismissed.
- Marked false positive.

Events must store the rule, input data reference, source/freshness state, triggered timestamp, and explanation.

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

## Data Quality Dependency

- Price/technical alerts require fresh or delayed acceptable OHLCV.
- Provider/freshness alerts may trigger when data is stale, failed, partial, or unknown.
- Fundamental alerts are not part of V1 unless explicitly scoped later.
- Alerts must respect ticker coverage tier restrictions.

## Schema Implications

Schema should support:

- Alert rule definition.
- Rule state.
- Alert event record.
- Event state.
- Triggered timestamp.
- Acknowledged/dismissed timestamp.
- False-positive flag and feedback note.
- Source/freshness snapshot.
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

Telegram notifications may be added only after local alert lifecycle and feedback persistence work.
