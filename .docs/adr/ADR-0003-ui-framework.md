# ADR-0003 — Next.js 15 + shadcn/ui untuk UI

- **Status:** accepted
- **Date:** 2026-05-16
- **Deciders:** owner

## Context

UI framework menentukan velocity development, polish, dan apakah project bisa di-evolve ke V1/V2 tanpa rewrite besar. PRD §14.3 mengusulkan dua jalur: **Streamlit** (speed) atau **Next.js** (polish).

Pertanyaan: pilih yang mana, atau dua-duanya?

## Decision

**Next.js 15 (App Router) + Tailwind + shadcn/ui** sebagai satu-satunya UI framework. Tidak ada dual track Streamlit.

Backend boundary: **single boundary**. UI-facing API via Next.js API routes (TypeScript). Heavy data ops via Python CLI scripts yang dipanggil oleh cron — bukan separate FastAPI service di MVP. Lihat [ADR-0008](ADR-0008-python-core-via-cli.md).

## Consequences

**Positive:**
- Owner familiar dengan Next.js + TypeScript.
- shadcn/ui = copy-paste primitives, owner sepenuhnya kontrol component, tidak terkunci ke library opinion.
- Polished UI long-term (portfolio piece).
- Type safety end-to-end di UI layer.
- Charting (lightweight-charts / Recharts) mature di ekosistem React.
- App Router → React Server Components → server-side fetch dari DuckDB tanpa API roundtrip yang tidak perlu.

**Negative:**
- Velocity awal lebih lambat dibanding Streamlit (~ 2× effort untuk fitur sederhana).
- Two-language stack (TS + Python) butuh discipline boundary.
- Build pipeline lebih kompleks dari Streamlit's single command.

**Trigger untuk re-evaluate:**
- Owner stuck di UI development > 4 minggu tanpa shipping fitur baru.
- Butuh prototype cepat untuk experimental feature → notebook (`notebooks/experiments/`) atau Streamlit standalone OK, tapi tidak menggantikan dashboard utama.

## Alternatives Considered

1. **Streamlit standalone** — di-reject: kurang polished, kurang controlable, sulit di-evolve ke V2 (PWA, custom interaction). Boleh dipakai di-paralel untuk notebook experimental.
2. **Next.js + separate FastAPI** — di-reject untuk MVP: dua server boundary tanpa nilai untuk single-user. Lihat [ADR-0008](ADR-0008-python-core-via-cli.md).
3. **SvelteKit / SolidStart** — di-reject: ekosistem shadcn equivalent lebih kecil, owner kurang familiar.
4. **Tauri desktop** — di-reject: PWA cukup untuk V2 mobile-friendly access.

## References

- [ARCHITECTURE.md §3](../ARCHITECTURE.md)
- [DESIGN_SYSTEM.md §5](../DESIGN_SYSTEM.md)
- Next.js: https://nextjs.org
- shadcn/ui: https://ui.shadcn.com
