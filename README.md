# SahamLens

> Personal trading companion untuk satu trader retail IDX. Local-first, public-repo-safe, AI-assisted. **Bukan** SaaS, signal seller, autonomous trader, atau broker integration.

**Status:** Phase 0 — Foundations (Sprint 0). Repo skeleton tahap awal. Belum siap dipakai.

> ⚠️ Personal learning & analysis tool, **bukan investment advice**. Baca [DISCLAIMER.md](DISCLAIMER.md) sebelum digunakan.

---

## Quick Start

### Prerequisites

| Tool | Versi minimum | Cek |
|---|---|---|
| Node.js | 20.x | `node --version` |
| pnpm | 9.x | `pnpm --version` |
| Python | 3.11+ | `python --version` |
| uv | 0.4+ | `uv --version` |
| git | 2.40+ | `git --version` |
| pre-commit | 4.x | `pre-commit --version` |

Install pre-commit kalau belum: `uv tool install pre-commit`.

### Setup

```bash
# 1. Clone & masuk repo
git clone <repo-url> sahamlens
cd sahamlens

# 2. Env
cp .env.example .env.local
# isi ANTHROPIC_API_KEY dst.

# 3. Python core
uv sync

# 4. Web app
pnpm install

# 5. DuckDB skeleton (buat schema di data/private/sahamlens.duckdb)
uv run python -m scripts.migrate

# 6. Pre-commit hooks
pre-commit install

# 7. Run
pnpm dev          # Next.js dev server (http://localhost:3000)
```

### Smoke Test

```bash
pnpm test         # vitest (TS)
uv run pytest     # pytest (Python)
pre-commit run --all-files
```

---

## Repo Layout

```
apps/web/         Next.js 15 dashboard (TypeScript strict)
packages/core/    Python data core (framework-independent)
packages/ui/      Shared TS UI components
scripts/          Python CLI entrypoints (cron-callable)
data/sample/      Fake committed data
data/private/     GITIGNORED — real DB, journal, portfolio
prompts/system/   LLM prompt templates
config/           *.example.yml committed; *.yml gitignored
.docs/            Modular docs (lihat .docs/README.md)
```

Detail per modul: [`.docs/ARCHITECTURE.md`](.docs/ARCHITECTURE.md).

---

## Documentation

- **Quick orientation:** [CLAUDE.md](CLAUDE.md) — alignment & workflow.
- **All docs:** [.docs/README.md](.docs/README.md) — documentation map.
- **Decisions:** [.docs/adr/](.docs/adr/) — architecture decision records.

---

## Contributing

Repo publik untuk sharing teknologi. Kontribusi welcome **tapi** tidak boleh menggeser arah ke SaaS / multi-user / auto-trade. Aturan + scope: [`.docs/CONTRIBUTING.md`](.docs/CONTRIBUTING.md).

---

## License

(TBD — kemungkinan MIT untuk kode, data privat ekslusif owner.)

---

## Disclaimer

[DISCLAIMER.md](DISCLAIMER.md) · [.docs/TRADING_DISCLAIMER.md](.docs/TRADING_DISCLAIMER.md)

Tool ini personal, single-user, local-first. Past performance tidak menjamin hasil masa depan. Konsultasi financial advisor berlisensi untuk keputusan material.
