# ADR-0001: Local-First Architecture

Status: Accepted
Date: 2026-05-31

## Context

SahamLens is a personal trading companion for one retail IDX trader. It handles local watchlists, journal entries, portfolio imports, and decision-support context that can be private.

## Decision

SahamLens will remain local-first and single-user.

- Private data lives under local ignored paths such as `data/private/`.
- The primary database is local DuckDB.
- Public docs and sample data must be safe to commit.
- No SaaS, auth, billing, team, or multi-tenant architecture is part of V1.

## Consequences

Positive:

- Lower privacy risk.
- Simpler deployment and maintenance.
- Faster personal dogfooding.

Trade-offs:

- No cross-device sync by default.
- No collaboration features.
- Manual backup remains the user's responsibility.

## Follow-Up

Any move toward cloud sync, accounts, or multi-user access requires a new ADR and PRD change.
