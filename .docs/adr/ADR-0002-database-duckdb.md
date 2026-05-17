# ADR-0002 — DuckDB sebagai Database MVP

- **Status:** accepted
- **Date:** 2026-05-16
- **Deciders:** owner

## Context

Sistem butuh storage untuk OHLCV time series, watchlist, journal, news, AI audit log, indicator cache. Beban dominan: analytical read (rolling indicator calc, multi-symbol scan). Beban write: rendah (single user, batch ingestion).

Kandidat:
- **SQLite** — mature, OLTP-style, sangat portable.
- **DuckDB** — analytical (columnar), single-file, embedded.
- **PostgreSQL** — full-featured, server-process.

## Decision

**DuckDB** sebagai DB MVP. Single-file (`data/private/sahamlens.duckdb`).

## Consequences

**Positive:**
- Query analytical (window function untuk MA/RSI rolling) cepat tanpa indexing manual.
- Single-file: backup, portability sama mudah dengan SQLite.
- Native pandas / Python integration via `duckdb` package.
- Bisa query parquet / CSV ad-hoc untuk exploration.
- Tidak butuh server process.

**Negative:**
- Concurrent write terbatas (acceptable: single user, batch writes via cron).
- Ecosystem tooling lebih kecil dari Postgres/SQLite (migration tool, ORM support).
- Beberapa SQL feature Postgres tidak ada (acceptable: kita tidak butuh).

**Trigger untuk migrate ke Postgres:**
- App di-deploy multi-machine secara serius.
- Concurrent write conflict muncul (saat ini tidak mungkin).
- Data growth > 50GB (DuckDB tetap fine, tapi review).
- Butuh foreign-key constraint / advanced auth (V2+).

## Alternatives Considered

1. **SQLite** — di-reject untuk MVP karena analytical query OHLCV lebih lambat dibanding DuckDB tanpa tuning. Tetap valid fallback kalau ada masalah ekosistem DuckDB.
2. **PostgreSQL** — di-reject untuk MVP: overkill, butuh server process, tidak ada concurrent writer.
3. **TimescaleDB** — di-reject: spesifik untuk high-volume tick data, kita EOD-only.

## Migration Path (if needed)

DuckDB schema ditulis dengan SQL-standard subset. Migration ke Postgres = mostly drop-in (data type mapping minor). Migration script tersedia di V1 kalau butuh.

## References

- [ARCHITECTURE.md §8](../ARCHITECTURE.md)
- [PRD_clean.md §11](../PRD_clean.md)
- DuckDB: https://duckdb.org
