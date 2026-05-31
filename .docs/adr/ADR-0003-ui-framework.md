# ADR-0003: Next.js and shadcn/ui for Web Dashboard

Status: Accepted
Date: 2026-05-31

## Context

SahamLens needs a local dashboard for watchlist review, data quality, fundamentals, screener results, alerts, journal review, and AI summaries.

## Decision

Use Next.js App Router with TypeScript strict, Tailwind, and shadcn/ui for the web application.

## Rationale

- Fits the existing app structure.
- Supports typed UI development.
- shadcn/ui provides practical dashboard components without a heavy design system.
- Works well for local-first web workflows.

## Consequences

Positive:

- Fast iteration on dashboard surfaces.
- Consistent component vocabulary.
- Clear separation from Python core modules.

Trade-offs:

- UI still needs discipline to avoid overbuilt pages.
- Business rules must stay in `packages/core`, not duplicated in React components.

## Follow-Up

Changing frontend framework or component system requires a new ADR.
