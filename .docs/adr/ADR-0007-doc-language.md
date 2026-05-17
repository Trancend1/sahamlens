# ADR-0007 — Bahasa Indonesia Primary untuk Dokumentasi

- **Status:** accepted
- **Date:** 2026-05-16
- **Deciders:** owner

## Context

PRD legacy ditulis campuran Indonesia–English. Repo publik dengan potential international contributor menimbulkan pertanyaan bahasa apa yang menjadi primary.

## Decision

**Bahasa Indonesia sebagai primary untuk dokumentasi naratif** (`.docs/**`, `README.md`, `CONTRIBUTING.md`, ADR body). Technical terms tetap English (RSI, MACD, watchlist, indicator, journal, etc) karena standar industry.

Kode, identifier, commit message, log = **English**.

## Consequences

**Positive:**
- Konsisten dengan audience utama (owner Indonesia, trader IDX).
- Mempercepat menulis (owner berpikir bilingual untuk topik trading).
- Tidak memaksa translasi yang menambah maintenance.

**Negative:**
- Public contributor non-Indonesia harus pakai translation tool.
- Sebagian search engine query lebih sulit (mix bahasa).

**Mitigasi:**
- Section heading boleh bilingual (Indonesia + English in parens) untuk discoverability di doc penting.
- Technical jargon tetap English supaya kode + doc seragam.
- Tabel & struktur data lebih mudah translate auto.

**Trigger untuk re-evaluate:**
- Kontribusi internasional regular (> 5 contributors aktif).
- Project pivot ke audience global (tidak akan, lihat scope).

## Alternatives Considered

1. **English only** — di-reject: owner berpikir lebih cepat dalam Indonesia untuk konteks trading IDX; menambah friction tanpa benefit jelas.
2. **Bilingual full** (setiap doc punya `*.en.md`) — di-reject: maintenance overhead tinggi, divergen pasti terjadi.

## References

- [.docs/README.md](../README.md)
