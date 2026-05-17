# ENGINEERING_STANDARDS — SahamLens

**Source of truth for:** Code style, naming, folder structure, git workflow, testing strategy, lint/format, CI rules, dependency management.
**Tidak di sini:** Architecture (→ [ARCHITECTURE.md](ARCHITECTURE.md)), security controls (→ [SECURITY.md](SECURITY.md)), contribution flow (→ [CONTRIBUTING.md](CONTRIBUTING.md)).

**Versi:** 1.0
**Status:** Active

---

## 1. Languages & Toolchain

| Layer | Language | Version | Manager |
|---|---|---|---|
| Web app | TypeScript | 5.x | `pnpm` |
| Data core | Python | 3.11+ | `uv` atau `poetry` |
| SQL | DuckDB dialect | — | — |

**Strictness:**
- TypeScript: `"strict": true`, `"noUncheckedIndexedAccess": true`.
- Python: `mypy --strict` untuk `packages/core/**`, type hints konsisten untuk `scripts/**`.

---

## 2. Folder Structure

```
sahamlens/
├── README.md
├── CLAUDE.md                       # AI alignment & memory (short, lihat root)
├── .docs/                          # dokumentasi modular (lihat .docs/README.md)
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
│
├── apps/
│   └── web/                        # Next.js 15 dashboard
│       ├── src/
│       │   ├── app/                # App Router pages
│       │   ├── components/         # Page-specific components
│       │   └── lib/                # UI utilities
│       └── tests/
│
├── packages/
│   ├── core/                       # Python — framework-independent
│   │   ├── data_sources/
│   │   ├── indicators/
│   │   ├── risk/
│   │   ├── journal/
│   │   ├── news/
│   │   ├── ai/
│   │   └── schemas/                # Pydantic + SQL migrations
│   │       └── migrations/
│   └── ui/                         # Shared TS UI components (IndicatorCard, dll)
│
├── scripts/                        # Python CLI entrypoints (cron-callable)
│   ├── ingest_prices.py
│   ├── ingest_news.py
│   ├── calculate_indicators.py
│   ├── generate_brief.py
│   ├── backup_private_data.py
│   └── wipe_private_data.py
│
├── data/
│   ├── sample/                     # COMMITTED — fake / public-example
│   └── private/                    # GITIGNORED — sahamlens.duckdb, logs, exports
│       └── .gitkeep
│
├── prompts/system/                 # LLM prompt templates
├── config/                         # *.example.yml committed; *.yml gitignored
├── notebooks/experiments/          # Eksperimental, labeled
└── tests/                          # Cross-cutting tests (no_private_leak, dll)
```

**Rules:**
- `packages/core/*` **tidak boleh** import `apps/web/**` atau `scripts/**`.
- `scripts/*` orchestration only — business logic di `packages/core/*`.
- File apa pun di `data/private/` dilarang ter-commit (CI check).

---

## 3. Naming Conventions

| Element | Convention | Contoh |
|---|---|---|
| TS variable / function | `camelCase` | `fetchWatchlist` |
| TS type / interface / component | `PascalCase` | `IndicatorCard`, `TradePlan` |
| TS constant (immutable global) | `UPPER_SNAKE_CASE` | `MAX_RISK_PERCENT` |
| Python module / function | `snake_case` | `calculate_rsi` |
| Python class | `PascalCase` | `IndicatorEngine` |
| SQL table / column | `snake_case` | `price_history`, `fetched_at` |
| File component TS | `PascalCase.tsx` | `IndicatorCard.tsx` |
| File util TS | `camelCase.ts` | `formatPrice.ts` |
| File Python | `snake_case.py` | `position_size.py` |
| ADR | `ADR-NNNN-kebab-case.md` | `ADR-0002-database-duckdb.md` |
| Migration | `NNNN_snake_case.sql` | `0001_initial_schema.sql` |

**Ticker format:** canonical = `BBCA.JK` (uppercase + `.JK` suffix). Internal kode harus normalize ke canonical sebelum query.

---

## 4. Linting & Formatting

| Tool | Scope | Config |
|---|---|---|
| ESLint (`@typescript-eslint`, `eslint-config-next`) | TS/TSX | `.eslintrc.cjs` |
| Prettier | TS/TSX/MD/YML | `.prettierrc` |
| Ruff | Python (lint + format) | `pyproject.toml` |
| `mypy --strict` | Python | `pyproject.toml` |
| `sqlfluff` (DuckDB dialect) | SQL migrations | `.sqlfluff` |
| `markdownlint` | `.docs/**` | `.markdownlint.json` |

Pre-commit hooks (`.pre-commit-config.yaml`) menjalankan: ruff, prettier, eslint, mypy (changed files), markdownlint, gitleaks, custom `no_private_leak` scanner. Lihat [SECURITY.md](SECURITY.md).

---

## 5. Testing Strategy

### 5.1 Coverage Targets

| Modul | Target |
|---|---|
| `packages/core/indicators/**` | ≥ 90% (financial calc) |
| `packages/core/risk/**` | ≥ 90% + property-based test untuk position sizing |
| `packages/core/ai/**` (schema validation, output validator) | ≥ 80% |
| `packages/core/data_sources/**` | ≥ 70% (mock external) |
| `packages/core/journal/**` | ≥ 70% |
| `apps/web/**` UI logic | 60%+ (snapshot OK untuk pure presentational) |
| Scripts | smoke-test only |

### 5.2 Test Categories

- **Unit:** `pytest` (Python), `vitest` (TS). Co-located dengan source: `*.test.ts`, `test_*.py`.
- **Property-based (Python):** `hypothesis` untuk position sizing, indicator edge cases.
- **Schema validation:** AI output **wajib** punya test schema (`test_ai_output_schema.py`) — gagal kalau LLM produce field invalid.
- **Cross-cutting:**
  - `tests/test_no_private_leak.py` — gagal kalau `data/private/**` muncul di diff.
  - `tests/test_data_freshness.py` — gagal kalau fetch script tidak menulis `fetched_at`.
  - `tests/test_indicator_consistency.py` — rule-based: kalau RSI > 70, AI tidak boleh bilang "oversold".

### 5.3 Wajib Test Sebelum Merge
- Position sizing: minimal 5 case termasuk stop di atas entry (short), stop = entry, fractional.
- Indicator formula: bandingkan dengan reference value dari pandas-ta atau TA-Lib untuk minimal 1 ticker sample.
- AI output: validate against JSON Schema, caveats non-empty.

---

## 6. Git Workflow

### 6.1 Branching
- `main` = production-ready (= "deployable lokal").
- Feature branch pendek: `feat/<topic>`, `fix/<topic>`, `chore/<topic>`. Hidup < 1 minggu.
- Squash merge ke `main`. Tidak ada long-lived release branch.

### 6.2 Commit Messages — Conventional Commits

```
feat(indicators): add RSI 14 calculation with edge-case tests
fix(risk): handle stop_price == entry_price gracefully
chore(deps): bump duckdb to 1.x
docs(adr): record decision to use DuckDB over SQLite
refactor(ai): extract prompt template loader
test(risk): add hypothesis property tests for position size
```

Prefix yang diterima: `feat | fix | chore | docs | refactor | test | perf | build | ci`.

Body opsional: jelaskan **why**, bukan what. What sudah ada di diff.

### 6.3 Pre-Commit Hooks (wajib)
- Lint + format (auto-fix).
- `gitleaks` / `detect-secrets`.
- `no_private_leak` scanner (custom, lihat [SECURITY.md](SECURITY.md)).
- Type check (mypy + tsc) untuk changed files.

### 6.4 PR Rules
- 1 PR = 1 logical change. Bias kuat ke kecil (< 400 LOC diff).
- PR description wajib link ke ADR kalau ada keputusan teknis.
- Tidak ada PR yang merge tanpa CI hijau.
- Untuk single-user repo: self-merge OK. Public contributor: lihat [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 7. CI (Minimal — GitHub Actions)

Workflow `.github/workflows/ci.yml`:
- Lint (eslint, ruff, sqlfluff, markdownlint).
- Type check (tsc, mypy).
- Test (vitest, pytest).
- Security scan (gitleaks).
- `no_private_leak` cross-check.

Workflow `.github/workflows/cron-hint.yml` — **tidak menjalankan ingestion**; hanya remind owner kalau cron lokal terakhir > 7 hari tidak commit checkpoint.

Tidak ada deploy workflow di MVP (lokal). Hosted dashboard (V1) deploy via Vercel native integration.

---

## 8. Dependency Management

### 8.1 Adding a Dependency
Sebelum tambah dependency, jawab dulu:
1. Apa fitur konkret yang dibutuhkan?
2. Bisa di-implement dalam < 50 LOC tanpa dep?
3. Apa weight bundle (untuk web) atau install time (untuk Python)?
4. Apakah dep ini maintained (commit terakhir < 6 bulan)?

Tolak default untuk: utility libraries (lodash), wrapper trivial, library experimental.

### 8.2 Pinning
- `pnpm` lockfile committed (`pnpm-lock.yaml`).
- Python: `uv.lock` atau `poetry.lock` committed.
- Major version bump = PR terpisah + smoke test.

### 8.3 Banned (sampai justifikasi kuat)
- Redux / global state library (pakai React Context + Server Components).
- ORM heavy (Prisma, SQLAlchemy) — DuckDB cukup raw + Pydantic schema.
- Auth library (single user, no auth).
- Real-time framework (Socket.io, dll).

---

## 9. Documentation Rules

- **Source of truth tunggal.** Lihat `.docs/README.md` untuk ownership map.
- **Tidak commit auto-generated docs** kalau bisa di-generate ulang (kecuali artifact ADR).
- **README.md root** = setup + run + link ke `.docs/` + disclaimer.
- **Setiap module di `packages/core/*`** punya `README.md` singkat: tugas modul + cara test.
- **Tidak ada multi-line comment block** kecuali documenting publik API yang non-trivial.
- **Tidak menulis comment yang menjelaskan WHAT** — pakai naming yang baik. Komentar hanya untuk **WHY** yang non-obvious.

---

## 10. Maintainability Principles

1. **Three strikes refactor.** Duplikasi muncul 3× → ekstrak. < 3× → biarkan inline.
2. **Boring tech first.** Pilih library tertua yang masih maintained sebelum yang trendiest.
3. **Reversibility.** Kalau ragu antara dua approach, pilih yang lebih mudah di-rollback.
4. **Refactor sprint setiap 3 sprint** — paksa konsolidasi sebelum tech debt jadi cement.
5. **Delete > add.** Kalau fitur tidak dipakai 4 minggu, hapus. (Lihat kill criteria di [PRD_clean.md §10](PRD_clean.md).)

---

## 11. Anti-Patterns (Tegas)

- ❌ Multi-user auth "for future flexibility".
- ❌ Background worker queue (BullMQ/Celery) sebelum bottleneck nyata.
- ❌ Microservice split sebelum monolith > 50k LOC.
- ❌ Custom DSL / config language.
- ❌ Generated code yang harus di-edit manual nanti.
- ❌ Test yang verify implementation, bukan behavior.
- ❌ Mock yang lebih kompleks dari kode yang di-test.
- ❌ "Just in case" feature flags untuk single-user system.
