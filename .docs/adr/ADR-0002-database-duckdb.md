# ADR-0002: DuckDB as Local Database

Status: Accepted
Date: 2026-05-31

## Context

SahamLens needs local analytical storage for OHLCV, indicators, journal data, provider health, coverage, fundamentals, screener results, alerts, and earnings metadata.

## Decision

Use DuckDB as the local database for V1.

## Rationale

- File-based and local-first.
- Good fit for analytical queries.
- Simple enough for single-user usage.
- Avoids server database operations.

## Consequences

Positive:

- Easy local setup.
- Good query ergonomics for tabular data.
- Public-repo-safe when private DB files are ignored.

Trade-offs:

- No multi-user concurrency target.
- Backup and file hygiene remain local responsibilities.

## Follow-Up

Changing to Postgres, TimescaleDB, cloud storage, or a hosted database requires a new ADR.
