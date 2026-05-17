# ADR-0001 — Local-First Architecture

- **Status:** accepted
- **Date:** 2026-05-16
- **Deciders:** owner
- **Supersedes:** —
- **Superseded by:** —

## Context

SahamLens adalah single-user personal trading companion (lihat [PRD_clean.md](../PRD_clean.md)). PRD legacy v1 mengusulkan stack cloud-native (Postgres + Redis + TimescaleDB + Kubernetes) untuk skenario SaaS. Ini menambahkan beban operasional besar tanpa nilai untuk personal use.

Pertanyaan: di mana data hidup, di mana komputasi terjadi?

## Decision

**Default local-first.** Data (portfolio, journal, OHLCV, news) disimpan di mesin owner. Komputasi (ingestion, indicator, AI orchestration) di mesin owner. Cloud opsional, opt-in per fitur (LLM API, optional hosted dashboard mirror).

## Consequences

**Positive:**
- Privacy by default — data sensitif tidak meninggalkan mesin.
- Zero hosting cost MVP.
- Tidak ada outage external (kecuali source data & LLM API).
- Tidak butuh DB administration overhead.
- Repo publik aman secara structural (data privat physically separate).

**Negative:**
- Akses dari device lain butuh effort manual (file sync atau tunnel).
- Backup tanggung jawab owner.
- Tidak ada inherent multi-machine sync.

**Trigger untuk re-evaluate:**
- Owner butuh akses dashboard dari device kedua secara reguler.
- Data growth > 10GB.
- Concurrent write conflict muncul (saat ini tidak mungkin — single writer).

## Alternatives Considered

1. **Cloud-native dari hari 1** (Postgres + Redis di VPS) — di-reject: cost, complexity, privacy risk, tidak proportional dengan single-user scope.
2. **Hybrid wajib** (DB cloud, compute lokal) — di-reject: tetap mengirim data privat ke pihak ketiga tanpa nilai tambahan.

## References

- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [SECURITY.md](../SECURITY.md)
- [PRD_clean.md §1, §4.4](../PRD_clean.md)
