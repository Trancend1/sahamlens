# ADR-0008: Python Core Accessed Through CLI/API Boundaries

Status: Accepted
Date: 2026-05-31

## Context

SahamLens uses Python for data ingestion, calculations, indicators, data quality, fundamentals, screener logic, alerts, journal analysis, and AI orchestration. The web app should not duplicate these rules.

## Decision

Keep domain logic in `packages/core` and expose workflows through scripts or API boundaries.

Rules:

- `packages/core` owns business logic.
- `scripts` orchestrate jobs and call core modules.
- `apps/web` renders results and triggers local/API workflows.
- Core modules must not import from `apps/web` or `scripts`.

## Consequences

Positive:

- Domain logic remains testable.
- CLI jobs are easy to dogfood locally.
- UI stays thinner.

Trade-offs:

- Boundaries need discipline when adding quick UI features.
- Some integration tests may need fixture data or local DB setup.

## Follow-Up

If a future architecture embeds Python directly into the web runtime or splits services, create a new ADR.
