# SahamLens — Distribution Readiness Analysis

> **Peran:** Product Architect & Distribution Engineer
> **Methodologi:** Verifikasi berbasis fakta dari codebase. Semua klaim punya bukti file & baris.
> **Tanggal:** 16 Juni 2026
> **Status:** Final — menunggu persetujuan owner untuk eksekusi

---

## Daftar Isi

1. [Current State Assessment](#1-current-state-assessment)
2. [Distribution Readiness Audit](#2-distribution-readiness-audit)
3. [Gap Analysis](#3-gap-analysis)
4. [Validation of create-sahamlens Strategy](#4-validation-of-create-sahamlens-strategy)
5. [Recommended Architecture](#5-recommended-architecture)
6. [Sprint Roadmap](#6-sprint-roadmap)
7. [Risks & Tradeoffs](#7-risks--tradeoffs)
8. [Final Recommendation](#8-final-recommendation)

---

## 1. Current State Assessment

### 1.1 Arsitektur Sekarang

```
┌─────────────────────────────────────────────────────┐
│                   User (browser)                      │
│                      http://localhost:3000             │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              apps/web (Next.js 15)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ 13 Halaman  │  │ 6 API Routes │  │ Tailwind UI │ │
│  └─────────────┘  └──────┬───────┘  └─────────────┘ │
│                          │                            │
│              ┌───────────▼───────────┐                │
│              │ pythonRunner.ts       │                │
│              │ execFile('python',    │                │
│              │  ['-m','scripts.*'])  │                │
│              └───────────┬───────────┘                │
└──────────────────────────┼──────────────────────────┘
                           │ subprocess
┌──────────────────────────▼──────────────────────────┐
│              packages/core (Python 3.11+)             │
│  DuckDB ─ data/private/sahamlens.duckdb               │
│  19 modul: ai, agent, alerts, screener, journal, ...  │
└──────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│         services/hermes (V2, long-running)            │
│  Telegram listener → intent router → policy → dispatch│
└─────────────────────────────────────────────────────┘
```

### 1.2 Kunci Fakta Codebase

| Aspek | Kondisi Saat Ini | Bukti |
|---|---|---|
| **Monorepo** | pnpm workspace (JS) + uv (Python), bukan monorepo terpadu | `pnpm-workspace.yaml` hanya `apps/*` + `packages/ui`; Python di `packages/core` via `hatchling` |
| **Python packaging** | `sahamlens-core` wheel dari `packages/core`, **tidak ada entry_points/console_scripts** | `pyproject.toml`: `[project.scripts]` tidak ada |
| **JS packaging** | `"private": true` — **tidak bisa dipublish ke npm** | `apps/web/package.json` L5, root `package.json` L5 |
| **Version** | `0.1.0` seragam di 3 tempat | `package.json`, `pyproject.toml`, `packages/core/__init__.py` |
| **Database** | DuckDB file, path hardcoded `./data/private/sahamlens.duckdb` (bisa di-override via env) | `packages/core/schemas/repository.py:19`, `.env.example` |
| **Python bridge** | Subprocess `execFile` via `pythonRunner.ts` — fragile, Windows punya path issue | `apps/web/src/lib/pythonRunner.ts:84-103` |
| **First-run** | Tidak ada mekanisme auto-setup. User harus manual 6 langkah | `README.md` L28-42 |
| **CI/CD** | GitHub Actions: web (lint+typecheck+test+build), core (ruff+mypy+pytest), secrets (gitleaks) | `.github/workflows/ci.yml` |
| **LICENSE** | **FILE LICENSE FISIK TIDAK ADA** — hanya deklarasi di metadata | `pyproject.toml` bilang MIT, `root/` tidak ada LICENSE |
| **Node requirement** | >=22.13.0 — cutting edge, belum LTS di banyak distro | `package.json` L12 |
| **PyPI/npm** | **Tidak pernah dipublikasikan** ke registry mana pun | Tidak ada `publishConfig`, tidak ada `npm publish` history |
| **Docker** | **Tidak ada** Dockerfile, docker-compose, atau container config | `glob("**/Dockerfile")` = empty |
| **Env vars required** | 9 env vars, 3 wajib untuk AI (`ANTHROPIC_API_KEY`, `LLM_PROVIDER`, `LLM_DEFAULT_MODEL`) | `.env.example` |
| **Hermes runtime** | Service long-running, perlu `uv run python -m services.hermes`, butuh env vars | `services/hermes/config.py` |

### 1.3 Fitur yang Ada (13 halaman web)

| Route | Deskripsi | Status |
|---|---|---|
| `/` | Dashboard | ✅ Implemented |
| `/data-quality` | Provider health & freshness | ✅ Implemented |
| `/watchlist` | Daftar pantauan | ✅ Implemented |
| `/portfolio` | Posisi portofolio | ✅ Implemented |
| `/portfolio/import` | Import CSV portofolio | ✅ Implemented |
| `/journal` | Trade journal | ✅ Implemented |
| `/journal/new` | Entri jurnal baru | ✅ Implemented |
| `/journal/weekly-review` | Review mingguan | ✅ Implemented |
| `/screener` | Screening saham | ✅ Implemented |
| `/stocks/[symbol]` | Detail saham + AI brief/chat | ✅ Implemented |
| `/strategy-rules` | Aturan strategi | ✅ Implemented |
| `/alerts` | Alert rules & events | ✅ Implemented |
| `/earnings` | Earnings manual-first | ✅ Implemented |

### 1.4 API Routes (6 endpoint)

| Endpoint | Fungsi |
|---|---|
| `GET /api/portfolio` | List portfolio |
| `POST /api/portfolio/import` | Import CSV |
| `POST /api/journal/plan` | Buat trade plan |
| `POST /api/journal/critique/[id]` | AI critique plan |
| `POST /api/stocks/[symbol]/brief` | AI stock brief |
| `POST /api/stocks/[symbol]/chat` | Tanya AI saham |

### 1.5 Python Core Modules (19 modul)

```
packages/core/
├── agent/              # Agent tool contracts, safe context, audit
├── ai/                 # LLM wrapper, provider abstraction, validator
├── alerts/             # Alert rules, event lifecycle, false-positive
├── coverage/           # Ticker coverage tracking
├── data_quality/       # Provider health, freshness
├── data_sources/       # Data provider abstraction + yfinance
├── earnings/           # Earnings metadata manual-first
├── fundamentals/       # Fundamental snapshot, completeness, confidence
├── indicators/         # Technical indicators
├── journal/            # Journal entries, weekly review
├── news/               # News ingestion/summarization
├── portfolio/          # Portfolio position management
├── risk/               # Risk analysis
├── runtime/            # Runtime readiness, schema status, bootstrap
├── schemas/            # Pydantic models + DuckDB migrations
├── screener/           # Screening rules and results
├── strategy/           # Simple strategy rules (no DSL)
├── ticker_coverage/    # Ticker lifecycle tracking
├── watchlist/          # Watchlist management
```

### 1.6 CLI Scripts (18 produksi + 7 test)

| Script | Fungsi |
|---|---|
| `scripts/agent_brief.py` | Generate stock brief via agent |
| `scripts/alerts.py` | Manage alert events/feedback |
| `scripts/calculate_indicators.py` | Compute technical indicators |
| `scripts/dump_stock_detail.py` | Dump detailed stock info |
| `scripts/earnings.py` | Earnings metadata operations |
| `scripts/fundamentals.py` | Fetch fundamental snapshots |
| `scripts/generate_brief.py` | Generate stock brief (direct) |
| `scripts/ingest_news.py` | Ingest news data |
| `scripts/ingest_prices.py` | Ingest price data |
| `scripts/journal_review.py` | Weekly journal review |
| `scripts/journal.py` | Journal CRUD operations |
| `scripts/migrate.py` | Run database migrations |
| `scripts/no_private_leak.py` | Check for private data leaks |
| `scripts/portfolio.py` | Portfolio CRUD operations |
| `scripts/provider_health.py` | Check data provider health |
| `scripts/runtime.py` | Runtime readiness checks |
| `scripts/screener.py` | Run stock screener |
| `scripts/summarize_news.py` | Summarize ingested news |
| `scripts/watchlist.py` | Watchlist management |

### 1.7 Services (Hermes Runtime — V2)

```
services/hermes/
├── __init__.py
├── __main__.py          # Entrypoint
├── config.py            # Env-driven runtime configuration
├── dispatch.py          # Read-only tool dispatch + ai_log_id linkage
├── intents.py           # Intent router
├── policy.py            # Non-advisory policy gate
├── telegram_listener.py # Telegram long-polling listener
├── writes.py            # Write-action confirmation (idempotent)
├── test_config.py
├── test_dispatch.py
├── test_intents.py
├── test_policy.py
├── test_telegram_listener.py
└── test_writes.py
```

### 1.8 DB Schema Migrations (8 file)

| Migration | Deskripsi |
|---|---|
| `0001_initial_schema.sql` | Initial schema |
| `0002_news_summary_fields.sql` | News summary fields |
| `0003_provider_health.sql` | Provider health tables |
| `0004_ticker_fundamentals.sql` | Ticker & fundamentals |
| `0005_screener.sql` | Screener tables |
| `0006_journal_strategy_review.sql` | Journal & strategy review |
| `0007_alerts_earnings.sql` | Alerts & earnings (V1-S6) |
| `0008_agent_runtime.sql` | Agent runtime audit schema (V2 M1) |

---

## 2. Distribution Readiness Audit

### 2.1 Open-Source Public Release — **50%**

| Kriteria | Status | Bukti |
|---|---|---|
| README jelas | ✅ Ada, dengan quick start, prasyarat, verifikasi | `README.md` |
| LICENSE file fisik | ❌ **TIDAK ADA** — cuma deklarasi di metadata | `find . -name "LICENSE"` → empty |
| CONTRIBUTING guide | ✅ Ada | `.docs/CONTRIBUTING.md` |
| Code of Conduct | ❌ Tidak ada | |
| Issue/PR templates | ❌ Tidak ada | `.github/` hanya `workflows/ci.yml` |
| Changelog | ❌ Tidak ada | |
| Security policy | ✅ Parsial (di SECURITY.md) | `.docs/SECURITY.md` |
| Badges | ❌ Tidak ada di README | |
| Dokumentasi API | ❌ Tidak ada docs publik | |
| Sample data | ✅ Ada sample CSVs | `data/sample/` |
| Private data protection | ✅ Gitignore + pre-commit hook + CI test | `.gitignore`, `no_private_leak.py`, CI `secrets` job |

**Blocker untuk open-source release:**
1. **LICENSE file fisik wajib** dibuat — tanpa ini, kode secara legal tidak bisa digunakan publik
2. Dokumentasi kontribusi perlu Code of Conduct, issue/PR templates
3. Changelog untuk transparansi rilis

### 2.2 npm create template (create-sahamlens) — **0%**

| Kriteria | Status | Bukti |
|---|---|---|
| `create-sahamlens` package | ❌ Tidak ada | Tidak ditemukan di registry atau kode |
| Template scaffolding | ❌ Tidak ada | |
| Bootstrap script interaktif | ❌ Tidak ada | |
| Zero-config first-run | ❌ Manual 6 langkah | `README.md` L28-42 |
| Deteksi OS/path | ❌ Tidak ada | |

### 2.3 npm global CLI — **5%**

| Kriteria | Status | Bukti |
|---|---|---|
| `[project.scripts]` entry_points | ❌ **TIDAK ADA** | `pyproject.toml` tidak ada `[project.scripts]` |
| `bin` di package.json | ❌ Tidak ada | |
| CLI yang self-contained | ❌ Bergantung pada repo checkout + uv + pnpm | |
| `sahamlens` command global | ❌ Tidak ada | |
| Doctor command | ❌ Tidak ada — tapi `scripts.runtime status --json` sudah ada | `scripts/runtime.py` |

**Blocker absolut:**
- Python packaging tidak punya `console_scripts` → tidak ada `sahamlens` CLI command
- Tidak mungkin distribusi npm global karena dependensi Python + DuckDB + uv

### 2.4 Desktop Application — **0%** (di luar scope projek, hanya referensi)

| Kriteria | Status | Bukti |
|---|---|---|
| Electron/Tauri wrapper | ❌ Tidak ada | |
| Bundled Python runtime | ❌ Tidak ada | |
| Bundled DuckDB | ❌ Tidak ada | |
| Offline-first | ✅ Arsitektur sudah local-first | `ARCHITECTURE.md` |
| Native installer | ❌ Tidak ada | |
| Auto-update | ❌ Tidak ada | |

### 2.5 SaaS — **0%** (di luar scope projek, hanya referensi)

| Kriteria | Status | Bukti |
|---|---|---|
| Multi-user auth | ❌ **TIDAK ADA**, dan sengaja tidak dibuat | `PRD.md` L5: "single-user" |
| API server | ❌ Tidak ada FastAPI | `ARCHITECTURE.md` L143: "deferred" |
| Cloud DB | ❌ Local DuckDB only | |
| Billing | ❌ Rejected scope | `EXECUTION_BLUEPRINT.md` L76-78 |
| Deployment infra | ❌ Tidak ada | |

### 2.6 Ringkasan Readiness Scorecard

| Target Distribusi | Readiness | Alasan |
|---|---|---|
| Open-source public release | **50%** | LICENSE hilang, issue/PR templates, changelog, CoC |
| `create-sahamlens` | **0%** | Tidak ada implementasi |
| npm global CLI | **5%** | `private: true`, tidak ada bin |
| PyPI CLI (`sahamlens`) | **0%** | Tidak ada entry_points |
| Desktop app | **0%** | Tidak ada wrapper |
| Docker | **0%** | Tidak ada Dockerfile |
| SaaS | **0%** | Out of scope (single-user) |

---

## 3. Gap Analysis

### 3.1 Critical Gaps (Blocker)

| # | Gap | Dampak | Effort | Prioritas |
|---|---|---|---|---|
| G1 | **Tidak ada entry_points/console_scripts** | Python CLI tidak bisa diinstal sebagai command global | 1 hari | 🔴 Critical |
| G2 | **`private: true` di package.json** | npm publish diblokir | 5 menit | 🔴 Critical |
| G3 | **Tidak ada LICENSE file fisik** | Illegal untuk publik gunakan kode | 5 menit | 🔴 Critical |
| G4 | **6 langkah manual untuk first-run** | User drop-off tinggi, error prone | 3-5 hari | 🔴 Critical |
| G5 | **Node >=22.13.0** | Banyak developer masih di Node 18/20 | 1 hari | 🟡 High |
| G6 | **Python bridge via subprocess** | Fragile antar OS, tidak portabel untuk distribusi | 5-10 hari | 🟡 High |
| G7 | **Hardcoded DuckDB path relatif** | Path broken kalau dijalankan dari direktori berbeda | 2 hari | 🟡 High |
| G8 | **`packages.core` import pattern** | Hanya work karena sys.path manipulation | 3 hari | 🟡 High |

### 3.2 High-Value Gaps

| # | Gap | Dampak | Effort | Prioritas |
|---|---|---|---|---|
| G9 | Tidak ada Makefile / task runner terpadu | Developer harus hafal 2 package manager | 1 hari | 🟡 High |
| G10 | Tidak ada Docker environment | Reproducibility antar OS rendah | 2 hari | 🟡 High |
| G11 | Tidak ada changelog | Pengguna tidak tahu apa yang berubah antar versi | 1 hari | 🟡 High |
| G12 | Tidak ada issue/PR templates | Kontribusi tidak terstandarisasi | 1 hari | 🟢 Medium |
| G13 | Tidak ada publish workflow di CI | Rilis masih manual | 2 hari | 🟢 Medium |
| G14 | `PYTHON_BIN` tidak didokumentasi di `.env.example` | Windows user kebingungan | 30 menit | 🟢 Medium |

### 3.3 Nice-to-Have

| # | Gap | Dampak | Effort | Prioritas |
|---|---|---|---|---|
| G15 | Badges di README | Visibility rendah | 30 menit | ⚪ Low |
| G16 | Desktop app (Tauri/Electron) | Pengalaman native | 20+ hari | ⚪ Low |
| G17 | Homebrew tap / winget package | Discoverability | 5 hari | ⚪ Low |

### 3.4 Dependensi Antar Gap

```
G1 (entry_points) ← G3 (LICENSE) tidak dependen
G4 (first-run) ← G7 (DB path) ← G8 (import pattern)
G6 (bridge) ← G8 (import pattern)
G10 (Docker) ← G5 (Node version)
G13 (publish CI) ← G1 + G2
```

---

## 4. Validation of create-sahamlens Strategy

### 4.1 Analisis: Apakah create-sahamlens Langkah yang Tepat?

#### Argumen PRO:
- `create-*` template adalah pola standar industri (`create-next-app`, `create-vite`, `create-t3-app`)
- Menyembunyikan kompleksitas setup multi-language (Node + Python + DuckDB)
- Menyediakan zero-config first-run experience
- Project scaffolding yang reusable

#### Argumen KONTRA:
- SahamLens bukan framework/library — **tidak ada yang "di-create"**. Ini adalah aplikasi utuh yang di-clone.
- `create-*` biasanya untuk mem-bootstrap project baru yang akan dikustomisasi. SahamLens adalah produk jadi.
- Kompleksitas: karena Python + DuckDB + uv, create-sahamlens harus install Python runtime juga — **ini bukan template JS biasa**
- Lebih masuk akal sebagai **installer CLI** atau **desktop app** daripada template
- Menambahkan npm package baru (create-sahamlens) berarti menambah attack surface dan maintenance overhead

### 4.2 Alternatif yang Dievaluasi

| Strategi | Kesesuaian | Effort | Risiko | Maintenability |
|---|---|---|---|---|
| **A. `create-sahamlens` (npm)** | Medium — solves first-run, tapi arsitekturnya berat (Python + DB + LLM) | 10-15 hari | Medium — package lain untuk di-maintain, Python bundling | Rendah |
| **B. `sahamlens` CLI global (PyPI)** | **Tinggi** — satu command untuk install + doctor + run + upgrade. Natural extension dari `scripts/` yang sudah ada | 5-8 hari | Rendah — reuse existing code, 1 package | Tinggi |
| **C. Docker Compose** | **Tinggi** — solusi paling portable, termasuk Python runtime + DuckDB | 2-3 hari | Sangat rendah — platform-independent | Tinggi |
| **D. GitHub template repo** | **Tertinggi untuk user technical** — klik "Use this template", ikuti README | 0 hari (free feature) | Paling rendah | Tertinggi (zero maintenance) |
| **E. GitHub template + CLI + Docker** | **Optimal** — layered approach, user pilih sesuai kebutuhan | 8-12 hari | Rendah | Tinggi |

### 4.3 Rekomendasi: Gabungan B + C + D

**Jangan buat `create-sahamlens`.** Ini adalah solusi yang salah untuk masalah yang sebenarnya sederhana (first-run experience). Ganti dengan pendekatan berlapis:

```
Prioritas:
  1. GitHub template repo (D) — mudah, zero effort, gratis
  2. sahamlens CLI (B) — menyatukan semua command, distribusi via PyPI
  3. Docker Compose (C) — opsional, untuk yang tidak mau setup Python manual
```

---

## 5. Recommended Architecture

### 5.1 Target Arsitektur Distribusi

```
sahamlens CLI (Python, via pipx / uv tool)
│
├── sahamlens init          # Bootstrap proyek lokal
│   ├── Buat direktori
│   ├── Clone template repo atau generate file
│   ├── Setup env vars (interaktif)
│   ├── uv sync / pnpm install
│   └── uv run migrate
│
├── sahamlens doctor        # Diagnosa setup
│   ├── Cek Python >=3.11
│   ├── Cek Node >=22.13
│   ├── Cek DuckDB file & schema
│   ├── Cek env vars
│   └── Rekomendasi perbaikan
│
├── sahamlens dev           # pnpm dev + PYTHON_BIN otomatis
├── sahamlens build         # next build
├── sahamlens start         # next start
├── sahamlens migrate       # uv run migrate
├── sahamlens status        # runtime status
├── sahamlens hermes        # start Hermes runtime
│
├── sahamlens upgrade       # git pull + uv sync + pnpm install + migrate
└── sahamlens version       # Tampilkan versi
```

### 5.2 Komponen yang Diubah

| Komponen | Sekarang | Target |
|---|---|---|
| `pyproject.toml` | `[project]` only | + `[project.scripts]` → `sahamlens = "scripts.cli:main"` |
| `scripts/cli.py` | Tidak ada | **File baru** — CLI dispatcher unified |
| `scripts/runtime.py` | Standalone | Tetap ada, dipanggil via `sahamlens status` |
| `scripts/doctor.py` | Tidak ada | **File baru** — diagnosa environment |
| `scripts/init.py` | Tidak ada | **File baru** — bootstrap interaktif |
| `scripts/upgrade.py` | Tidak ada | **File baru** — upgrade workflow |
| `packages/core/schemas/repository.py` | `DEFAULT_DB = "./data/private/..."` | Ganti jadi `~/.sahamlens/data/sahamlens.duckdb` dengan fallback |
| `apps/web/src/lib/pythonRunner.ts` | `defaultPython()` pakai `python`/`python3` | + Cari `.venv/Scripts/python.exe` otomatis |
| `Dockerfile` | Tidak ada | **File baru** — multi-stage build |
| `docker-compose.yml` | Tidak ada | **File baru** — dev environment |

### 5.3 Package Structure untuk PyPI

```
sahamlens-core@0.2.0 (PyPI — sahamlens)
├── packages/core/       # Business logic (existing, minor refactor)
├── scripts/             # + cli.py, doctor.py, init.py, upgrade.py
│   ├── __init__.py
│   ├── cli.py           # NEW: Typer/Click-based CLI dispatcher
│   ├── doctor.py        # NEW: Environment diagnostic
│   ├── init.py          # NEW: Interactive init
│   ├── upgrade.py       # NEW: Upgrade runner
│   ├── runtime.py       # EXISTING: runtime status/bootstrap
│   └── migrate.py       # EXISTING: migration runner
├── pyproject.toml       # + entry_points
└── README.md
```

**Key change:** `sahamlens` CLI terinstall via `pipx install sahamlens` atau `uv tool install sahamlens`, dan menyediakan command untuk mengelola instalasi lokal.

### 5.4 Dependency Graph (Setelah Refactor)

```
pipx install sahamlens
  │
  ├── sahamlens init
  │     ├── git clone template OR buat direktori kosong
  │     ├── cp .env.example → .env.local (interaktif)
  │     ├── uv sync (install Python deps)
  │     ├── pnpm install (install JS deps)
  │     └── uv run migrate (buat DB + schema)
  │
  ├── sahamlens dev
  │     ├── Deteksi PYTHON_BIN otomatis
  │     │   ├── .venv/Scripts/python.exe (Windows)
  │     │   ├── .venv/bin/python (macOS/Linux)
  │     │   └── fallback: system python
  │     └── pnpm --filter @sahamlens/web dev
  │
  ├── sahamlens doctor
  │     ├── Cek Python >=3.11
  │     ├── Cek Node >=22.13
  │     ├── Cek pnpm >=9.0
  │     ├── Cek DuckDB file exists + schema valid
  │     ├── Cek env vars required
  │     └── Output tabel + rekomendasi
  │
  └── sahamlens upgrade
        ├── git pull
        ├── uv sync
        ├── pnpm install
        └── uv run migrate
```

### 5.5 Data Directory Standard

```
# Linux/macOS
~/.sahamlens/
  data/
    sahamlens.duckdb
  config/
    watchlist.yml
    indicators.yml
    rss_feeds.yml
    cost_budget.yml
  logs/
    hermes.log

# Windows
%USERPROFILE%\.sahamlens\
  data\
    sahamlens.duckdb
  config\
    ...
```

Ini memecahkan G7 (hardcoded relative path) dan membuat path konsisten regardless of working directory.

### 5.6 Strategi Migrasi Path DB

Untuk user existing yang sudah punya DB di `./data/private/sahamlens.duckdb`:

1. `sahamlens doctor` deteksi bahwa DB ada di path lama
2. Rekomendasi migrasi: `sahamlens init --migrate`
3. `sahamlens init --migrate` copy DB ke `~/.sahamlens/data/sahamlens.duckdb`
4. Hapus `DUCKDB_PATH` dari `.env.local` (sudah pakai default baru)
5. Update `.env.local` dengan path baru jika user override

---

## 6. Sprint Roadmap

### Phase 0: Foundation (Size: S, Duration: ~1 week, Risk: Sangat Rendah)

| Task | Effort | Dependencies | Gap |
|---|---|---|---|
| Buat LICENSE file (MIT) | 5 menit | None | G3 |
| Hapus `private: true` dari root `package.json` | 5 menit | None | G2 |
| Tambah `[project.scripts]` → `sahamlens = "scripts.cli:main"` | 1 hari | None | G1 |
| Buat `scripts/cli.py` minimal dengan subcommand `version`, `status` | 2 hari | Phase 0 entry_points | G1 |
| Tambah `PYTHON_BIN` ke `.env.example` | 30 menit | None | G14 |
| Verifikasi `pipx install .` atau `uv tool install .` work | 1 hari | Phase 0 cli.py | G1, G6 |

**Exit criteria:** `sahamlens version` dan `sahamlens status` work setelah `pip install .`

**Files touched:** `pyproject.toml` (edit), `scripts/cli.py` (new), `.env.example` (edit), `LICENSE` (new)

### Phase 1: First-Run Experience (Size: M, Duration: ~1 week, Risk: Rendah)

| Task | Effort | Dependencies | Gap |
|---|---|---|---|
| Buat `scripts/doctor.py` — check Python, Node, DuckDB, env vars | 2 hari | Phase 0 | G4 |
| Buat `scripts/init.py` — interactive bootstrap | 3 hari | Phase 0 | G4 |
| Buat `sahamlens doctor` command | 1 hari | `scripts/doctor.py` | G4 |
| Buat `sahamlens init` command | 1 hari | `scripts/init.py` | G4 |
| Buat `sahamlens upgrade` command (git pull + sync + migrate) | 1 hari | Phase 0 | G4, G11 |
| Refactor `repository.py` → default DB ke `~/.sahamlens/` | 1 hari | None | G7 |

**Exit criteria:** `sahamlens init` bisa setup dari nol di direktori kosong

**Files touched:** `scripts/doctor.py` (new), `scripts/init.py` (new), `scripts/upgrade.py` (new), `scripts/cli.py` (edit), `packages/core/schemas/repository.py` (edit)

### Phase 2: CLI Polish & Integration (Size: M, Duration: ~1 week, Risk: Rendah)

| Task | Effort | Dependencies | Gap |
|---|---|---|---|
| Buat `sahamlens dev` (auto-detect `.venv` + `pnpm dev`) | 1 hari | Phase 1 | G6 |
| Buat `sahamlens migrate` | 1 hari | Phase 1 | G4 |
| Buat `sahamlens hermes` (start Hermes, handle daemon) | 2 hari | Phase 1 | — |
| Refactor `pythonRunner.ts` → cari `.venv` otomatis | 1 hari | None | G6 |
| Tambah argumen `--port`, `--host` ke `sahamlens dev` | 1 hari | Phase 2 dev | — |

**Exit criteria:** Semua workflow dari develop → build → serve via satu CLI command

**Files touched:** `scripts/cli.py` (edit), `apps/web/src/lib/pythonRunner.ts` (edit), `scripts/migrate.py` (minor edit)

### Phase 3: Release Infrastructure (Size: S, Duration: ~3 days, Risk: Rendah)

| Task | Effort | Dependencies | Gap |
|---|---|---|---|
| Publish `sahamlens` ke PyPI (test.pypi.org first) | 1 hari | Phase 2 | G1 |
| Buat GitHub release workflow (tag → publish PyPI) | 1 hari | Phase 2 | G13 |
| Buat CHANGELOG.md | 1 hari | None | G11 |
| Tambah issue/PR templates | 1 hari | None | G12 |
| Buat Code of Conduct | 1 hari | None | — |

**Exit criteria:** `pipx install sahamlens` work dari PyPI publik

**Files touched:** `.github/workflows/publish.yml` (new), `CHANGELOG.md` (new), `.github/ISSUE_TEMPLATE/` (new), `.github/PULL_REQUEST_TEMPLATE.md` (new), `CODE_OF_CONDUCT.md` (new)

### Phase 4: Docker (Optional, Size: S, Duration: ~2 days, Risk: Rendah)

| Task | Effort | Dependencies | Gap |
|---|---|---|---|
| Buat `Dockerfile` (multi-stage: Python + Node) | 1 hari | Phase 2 | G10 |
| Buat `docker-compose.yml` | 1 hari | Phase 2 | G10 |
| Dokumentasi Docker usage | 0.5 hari | Phase 4 | — |

**Exit criteria:** `docker compose up` menjalankan SahamLens lengkap

**Files touched:** `Dockerfile` (new), `docker-compose.yml` (new), `README.md` (edit)

### Phase 5: Desktop App (Deferred, Size: XL, Duration: ~4 weeks, Risk: Medium)

| Task | Effort | Dependencies | Gap |
|---|---|---|---|
| Evaluasi Tauri vs Electron untuk packaging Python | 2 hari | Phase 3 | G16 |
| Bundle Python runtime (PyInstaller atau embedded) | 5 hari | Phase 3 | G16 |
| Tauri wrapper untuk web app | 5 hari | Phase 3 | G16 |
| Native installer (NSIS/DMG/AppImage) | 3 hari | Phase 3 | G16 |
| Auto-update mechanism | 3 hari | Phase 3 | G16 |

**Exit criteria:** Desktop app terinstall dan berfungsi offline penuh

### Visual Roadmap

```
Minggu 1         Minggu 2         Minggu 3         Minggu 4       Bulan 2+
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────────┐  ┌────────────┐
│ Phase 0  │    │ Phase 1  │    │ Phase 2  │    │ Phase 3    │  │ Phase 5    │
│ Foundation│───▶│ First-Run│───▶│ CLI      │───▶│ Release    │  │ Desktop    │
│          │    │          │    │ Polish   │    │ Infra      │  │ (deferred) │
├──────────┤    ├──────────┤    ├──────────┤    ├────────────┤  ├────────────┤
│ LICENSE  │    │ doctor   │    │ dev cmd  │    │ PyPI pub   │  │ Tauri eval │
│ private  │    │ init     │    │ migrate  │    │ CI/CD      │  │ PyInstall  │
│ → false  │    │ upgrade  │    │ hermes   │    │ templates  │  │ Installer  │
│ entry_pt │    │ DB path  │    │ runner   │    │ CHANGELOG  │  │ Auto-upd   │
│ cli.py   │    │ refactor │    │ pyRunner │    │ CoC        │  │            │
└──────────┘    └──────────┘    └──────────┘    └────────────┘  └────────────┘
                                                  ┌────────────┐
                                                  │ Phase 4    │
                                                  │ Docker     │
                                                  │ (optional) │
                                                  └────────────┘

Effort total: ~3-4 minggu untuk distribusi CLI
Key: ▓ = Critical | ▒ = High value | ░ = Nice-to-have
```

---

## 7. Risks & Tradeoffs

### 7.1 Risiko Utama

| Risiko | Dampak | Probabilitas | Mitigasi |
|---|---|---|---|
| **Python dependency hell** — user tidak punya Python 3.11+ | Seluruh app tidak jalan | Tinggi | Docker sebagai fallback, `doctor` command untuk deteksi dini |
| **DuckDB file lock** di multi-process | Race condition writes | Sedang | Sudah di-handle oleh V1-S4.1, perlu test lebih lanjut |
| **yfinance reliability** — data provider bisa block | Fitur fundamental/scraper rusak | Tinggi | Data Sources framework sudah abstraction, tinggal tambah provider alternatif |
| **LLM API key required** untuk AI fitur | AI features tidak berguna tanpa key | Tinggi | Harus graceful degradation — tunjukin error jelas, jangan broken page |
| **Next.js 15 + React 19** masih relatif baru | Compatibility issues | Rendah | Pinning exact version sudah dilakukan |
| **Platform fragmentation** — Windows vs macOS vs Linux | Path issues, Python binary name | Sedang | `doctor` command + Docker |
| **PyPI publishing maintenance** — perlu API token, versi management | Overhead rilis | Rendah | Automate via GitHub Actions |
| **DuckDB version compatibility** — major upgrade bisa break DB | Data loss / migration | Rendah | Migration system sudah ada, test coverage |

### 7.2 Tradeoffs

| Keputusan | Keuntungan | Kerugian |
|---|---|---|
| **Not create-sahamlens (pilih sahamlens CLI via PyPI)** | Satu command untuk semua, reuse existing `scripts/`, 1 package untuk di-maintain | Tidak mengikuti pola `create-*` yang familiar di ekosistem JS |
| **Default DB di `~/.sahamlens/`** | Path konsisten, tidak bergantung working directory, privasi lebih baik | Breaking change untuk user existing (butuh migrasi path) |
| **pipx/uv tool install** | Python-native, bisa manage version, isolasi environment | User harus install Python dulu (tidak self-contained) |
| **Docker opsional, bukan wajib** | Tidak memaksa user belajar Docker | Setup manual lebih kompleks, platform fragmentation tetap ada |
| **Desktop app ditunda** | Fokus pada distribusi CLI yang lebih cepat, ROI lebih cepat | User tidak punya pengalaman desktop native, onboarding kurang mulus |
| **Refactor pythonRunner.ts** | Bridge lebih robust, auto-detect `.venv` | Perlu testing ulang semua API routes |

### 7.3 Hal yang Sengaja Tidak Dilakukan

| Item | Alasan |
|---|---|
| **`create-sahamlens` npm package** | Overengineering untuk masalah sederhana. Lihat §4.3 |
| **Electron desktop app sekarang** | Tidak ada demand terbukti, effort besar (20+ hari), defer ke Phase 5 |
| **FastAPI sidecar** | Melanggar arsitektur lokal-pertama (ADR-0019 D1), subprocess sudah cukup |
| **Multi-user / SaaS** | Di luar scope projek (PRD), single-user adalah identity |
| **Homebrew / winget package** | Terlalu dini, lihat adoption dulu setelah PyPI publish |
| **Bundling Python dengan PyInstaller** | Defer ke desktop app phase, terlalu berat untuk CLI-only |

---

## 8. Final Recommendation

### Prioritaskan: SahamLens CLI via PyPI + GitHub Template

```
Rekomendasi distribusi:
  Tier 1 (hari ini):    GitHub template repo — gratis, zero effort
  Tier 2 (1-2 sprint):  SahamLens CLI via PyPI — pipx install sahamlens
  Tier 3 (opsional):    Docker Compose — untuk reproducibility
  Tier 4 (deferred):    Desktop app — hanya jika ada demand terbukti
```

### Langkah Konkret Pertama (Besok — < 2 jam)

```
1. Buat LICENSE file (MIT)
2. Hapus "private": true dari root package.json
3. Ubah pyproject.toml — tambah [project.scripts]
4. Buat scripts/cli.py dengan 1 subcommand: version
5. Verifikasi:
     pip install -e .
     sahamlens version
     # → SahamLens 0.1.0
```

### Distribution Readiness Scorecard (Final)

| Target | Current | Target 1 Month | Gap |
|---|---|---|---|
| Open-source public release | **50%** | **90%** | LICENSE, templates, changelog, CoC |
| `create-sahamlens` | 0% | **SKIP** | — |
| npm global CLI | 5% | **SKIP** (ganti PyPI) | — |
| **PyPI CLI (`sahamlens`)** | **0%** | **80%** | Entry points, doctor, init, release infra |
| Docker | 0% | **30%** (optional) | Dockerfile + compose |
| Desktop app | 0% | **Deferred** | — |
| SaaS | 0% | **OUT OF SCOPE** | — |

### Daftar Pekerjaan untuk Eksekusi

| Phase | Pekerjaan | Obyektif |
|---|---|---|
| **Sekarang** | LICENSE, non-private, entry_points | ✅ Minimal viable distribution |
| **Sprint ini** | `doctor`, `init`, `upgrade` CLI | ✅ First-run experience |
| **Sprint depan** | CLI polish, pythonRunner.ts refactor | ✅ Developer experience |
| **Sprint depan +** | PyPI publish, CI/CD, changelog | ✅ Public release |
| **Opsional** | Docker | ✅ Reproducibility |

---

## Appendix A: File Reference

| File yang Akan Diubah/Dibuat | Phase | Tipe |
|---|---|---|
| `LICENSE` | Phase 0 | New |
| `pyproject.toml` | Phase 0 | Edit |
| `scripts/cli.py` | Phase 0 | New |
| `.env.example` | Phase 0 | Edit |
| `scripts/doctor.py` | Phase 1 | New |
| `scripts/init.py` | Phase 1 | New |
| `scripts/upgrade.py` | Phase 1 | New |
| `packages/core/schemas/repository.py` | Phase 1 | Edit |
| `apps/web/src/lib/pythonRunner.ts` | Phase 2 | Edit |
| `.github/workflows/publish.yml` | Phase 3 | New |
| `CHANGELOG.md` | Phase 3 | New |
| `CODE_OF_CONDUCT.md` | Phase 3 | New |
| `.github/ISSUE_TEMPLATE/*` | Phase 3 | New |
| `.github/PULL_REQUEST_TEMPLATE.md` | Phase 3 | New |
| `Dockerfile` | Phase 4 | New |
| `docker-compose.yml` | Phase 4 | New |

## Appendix B: Environment Variables (Final)

| Variable | Required | Default | Digunakan di |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Untuk AI Anthropic | — | `packages/core/ai/provider.py` |
| `LLM_PROVIDER` | Untuk AI (default: anthropic) | `anthropic` | `packages/core/ai/provider.py` |
| `LLM_DEFAULT_MODEL` | Untuk AI | `claude-sonnet-4-6` | `packages/core/ai/provider.py` |
| `LLM_DAILY_COST_CAP_IDR` | Optional | `15000` | `packages/core/ai/router.py` |
| `SAHAMLENS_LLM_API_KEY` | Untuk non-Anthropic LLM | — | `packages/core/ai/provider.py` |
| `SAHAMLENS_TELEGRAM_BOT_TOKEN` | Optional (Telegram) | — | `services/hermes/config.py` |
| `SAHAMLENS_TELEGRAM_CHAT_ID` | Optional (Telegram) | — | `services/hermes/config.py` |
| `SAHAMLENS_HERMES_ENABLED` | Optional (Hermes) | `0` | `services/hermes/config.py` |
| `NEXT_PUBLIC_APP_NAME` | Optional | `SahamLens` | Web app |
| `NEXT_PUBLIC_DISCLAIMER_SHORT` | Optional | — | Web app |
| `PYTHON_BIN` | **Wajib ditambahkan ke .env.example** | auto-detect | `pythonRunner.ts` |
| `DUCKDB_PATH` | Optional | `~/.sahamlens/data/sahamlens.duckdb` | `repository.py` |

---

*Dokumen ini adalah deliverable Product Architect & Distribution Engineer. Siap untuk direview oleh owner dan dijadikan backlog untuk sprint berikutnya.*
