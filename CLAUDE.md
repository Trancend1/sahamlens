# CLAUDE.md — SahamLens

**Brief:** SahamLens = personal trading companion untuk satu trader retail IDX. Local-first, public-repo-safe, AI-assisted (AI menjelaskan, user memutuskan). **Bukan** SaaS, signal seller, autonomous trader, atau broker integration. Detail produk: [`.docs/PRD.md`](.docs/PRD.md).

> File ini = **alignment & workflow layer**, bukan dokumentasi. Fakta produk/teknis hidup di `.docs/`.

---

## 1. Documentation Map

Selalu cite, jangan duplikasi:

| Topik | Source of truth |
|---|---|
| Product scope / goals / non-goals | [.docs/PRD.md](.docs/PRD.md) |
| System design / schema | [.docs/ARCHITECTURE.md](.docs/ARCHITECTURE.md) |
| UI philosophy / visual rules | [.docs/DESIGN_SYSTEM.md](.docs/DESIGN_SYSTEM.md) |
| Code style / git / test | [.docs/ENGINEERING_STANDARDS.md](.docs/ENGINEERING_STANDARDS.md) |
| Data sources / rate limits | [.docs/DATA_SOURCES.md](.docs/DATA_SOURCES.md) |
| AI rules / output schema | [.docs/AI_BOUNDARIES.md](.docs/AI_BOUNDARIES.md) |
| Privacy / threat model / secrets | [.docs/SECURITY.md](.docs/SECURITY.md) |
| Disclaimer / legal | [.docs/TRADING_DISCLAIMER.md](.docs/TRADING_DISCLAIMER.md) |
| Roadmap / sprint / DoD | [.docs/EXECUTION_BLUEPRINT.md](.docs/EXECUTION_BLUEPRINT.md) |
| Kontribusi | [.docs/CONTRIBUTING.md](.docs/CONTRIBUTING.md) |
| Keputusan teknis | [.docs/adr/](.docs/adr/) |

Aturan:
- Sebelum menulis fakta → cek tabel. Sudah ada → cite.
- Sebelum ubah fakta → edit source of truth, bukan file derived.
- Sebelum buat dokumen baru → cek apakah muat di existing. Bias kuat ke **tidak nambah file**.

---

## 2. Progress

### 2.1 Roadmap (MVP-0)

```
Phase 0  →  Phase MVP  →  Phase V1  →  Phase V2
              ↑ active gate sequence

Phase Experimental — paralel, terisolasi
```

| Phase | Status | Exit Signal | Tujuan |
|---|---|---|---|
| **Phase 0 — Foundations** | done ✓ | Hello-world render + CI hijau + pre-commit block dummy secret | Repo skeleton, tooling, security baseline |
| **Phase MVP — Private Learning Dashboard** | active | Owner pakai produk untuk daily review 5 hari berturut-turut | Watchlist + indicator + journal + AI brief + risk |
| **Phase V1 — Better Decision Support** | locked | Screener + alert dipakai mingguan; false-positive rate tracked | Fundamental + screener + alerts + earnings summary |
| **Phase V2 — Personal Trading System Builder** | locked | Backtest + playbook tunjukkan setup mana yang performa | Playbook + backtest + analytics + paper trading + PWA |

Detail sprint: [`.docs/EXECUTION_BLUEPRINT.md §3–6`](.docs/EXECUTION_BLUEPRINT.md).

### 2.2 Reusable Phase Gate

Tiap phase wajib lewat gate sama sebelum naik:

1. **Scope check.** Semua deliverable di phase selesai (tick di Exit Criteria).
2. **Test gate.** Lint + type check + test pass. Financial calc ≥90% coverage; lainnya ≥70%.
3. **Security gate.** Pre-commit (gitleaks + `no_private_leak`) hijau di CI. Tidak ada file `data/private/*` tercommit.
4. **Doc gate.** Source-of-truth doc di `.docs/` ter-update. ADR ditulis jika keputusan teknis besar.
5. **Demo to self.** Owner pakai produk untuk daily workflow nyata minimal 3 hari berturut-turut.
6. **Phase Log entry.** Catat di §2.5 — tanggal exit, lessons learned, item yang ditunda.

Gagal di salah satu → phase belum exit. Tidak ada "menyusul nanti".

### 2.3 Active Phase

**Phase:** Phase MVP — Private Learning Dashboard.
**Sprint aktif:** **S1 — Data ingestion + DuckDB + watchlist CRUD**.

**Sprint deliverable:**
- `packages/core/data_sources/yfinance/` adapter dengan canonical ticker normalize + rate-limit + 429 backoff.
- `scripts/ingest_prices.py` (yfinance → DuckDB `price_history`, `--json` output).
- `packages/core/watchlist/` module (`add`/`remove`/`list`/`get`) + Pydantic schema.
- `scripts/watchlist.py` CLI (subcommands: `add`, `remove`, `list`, `seed`).
- Seed 10 ticker IDX: BBCA, BBRI, BBNI, BMRI, TLKM, ASII, UNVR, ANTM, ICBP, GGRM.
- Next.js `/watchlist` route — render watchlist + freshness badge per ticker.
- Tests: yfinance adapter (mocked HTTP), watchlist CRUD (in-memory DuckDB), ingest_prices smoke.

**Next:** S2 — Indicator engine (MA 5/10/15/50/200, volume avg, RSI 14, MACD), test-first coverage ≥ 90%.

### 2.4 Exit Criteria

Phase MVP exit (semua wajib — sumber [`.docs/EXECUTION_BLUEPRINT.md §4.2`](.docs/EXECUTION_BLUEPRINT.md)):

Produk:
- [ ] Owner bisa review watchlist dalam 15–30 menit.
- [ ] Owner bisa buat trade plan lengkap (semua field PRD §8.2).
- [ ] AI output selalu cite data + tampilkan caveat.

Teknis:
- [ ] Tidak ada private data ter-commit (verified pre-commit + CI `no_private_leak`).
- [ ] Core indicator calc test coverage ≥ 90%.
- [ ] Position size calculator: ≥ 5 unit test + property-based.
- [ ] Banned-phrase filter aktif di AI pipeline.
- [ ] Schema validation reject malformed AI output.

Safety:
- [ ] Disclaimer di README, UI footer, AI panel, export.
- [ ] Tidak ada bahasa command buy/sell di copy.

### 2.5 Phase Log

| Phase | Exit date | Lessons | Carried forward |
|---|---|---|---|
| Phase 0 | 2026-05-18 | (a) pnpm 11 inject `allowBuilds` placeholder → harus diisi nilai konkret sebelum install lanjut. (b) Owner Windows tidak punya gitleaks global → pakai `detect-secrets` di pre-commit + `gitleaks-action` di CI sebagai defense-in-depth. (c) ruff `UP` rule auto-rewrite `datetime.timezone.utc` → `datetime.UTC` (Py 3.11+). (d) `next lint` deprecated di Next 16. | Migrasi `next lint` → ESLint CLI sebelum upgrade Next.js 16. |

---

## 3. Stack (Locked)

Tidak boleh diganti tanpa ADR di [`.docs/adr/`](.docs/adr/).

- **UI:** Next.js 15 (App Router) + TypeScript strict + Tailwind + shadcn/ui.
- **Core:** Python 3.11+ dengan `mypy --strict`.
- **DB:** DuckDB (file-based, single-user).
- **Charts:** `lightweight-charts`.
- **Test:** `vitest` (TS), `pytest` + `hypothesis` (Python).
- **Lint:** `eslint` + `prettier` (TS), `ruff` + `mypy` (Python).
- **Pre-commit:** `pre-commit` + `gitleaks` + custom `no_private_leak`.
- **Pkg mgr:** `pnpm` (TS), `uv` (Python).
- **LLM:** provider-agnostic wrapper di `packages/core/ai`. Tidak hardcode vendor.

Banned di MVP: Kubernetes, TimescaleDB, Redis, Vector DB, microservice split, custom DSL. Lihat [`.docs/PRD.md §4.4`](.docs/PRD.md).

---

## 4. AI Instructions

### 4.1 Before Coding

1. Baca file ini sampai habis. Untuk task sempit, lazy-load hanya `.docs/` yang relevan.
2. Konfirmasi task fit Active Phase (§2.3). Out-of-scope → propose ADR dulu, jangan langsung tulis kode.
3. Cek source-of-truth doc dari Documentation Map sebelum klaim fakta.
4. Untuk financial calc → **test dulu**, implement kemudian.
5. Cek `data/private/*` tidak akan tersentuh oleh perubahan.

### 4.2 Code Rules (Non-Negotiable)

- **TypeScript strict, mypy strict.** Tidak ada `any` / `# type: ignore` tanpa komentar WHY satu baris.
- **Vertical slice.** Implement data → calc → UI dalam satu PR kecil. Hindari horizontal layer-only PR.
- **Three-strikes refactor.** Duplikasi muncul 3× → ekstrak. < 3× → inline.
- **Three-question dependency gate.** Sebelum tambah dep: (a) fitur konkret apa, (b) bisa < 50 LOC tanpa dep, (c) berat bundle/install?
- **Boundary.** `packages/core/*` **tidak boleh** import `apps/web/**` atau `scripts/**`. `scripts/*` = orchestration; business logic di `packages/core/*`.
- **Conventional Commits** + squash merge ke `main`.
- **Coverage.** ≥90% untuk `packages/core/indicators` & `packages/core/risk`; ≥70% sisanya.
- **Tidak ada `data/private/*` tercommit.** Pre-commit + CI guard.

### 4.3 Anti-Slop

- ❌ Komentar yang menjelaskan WHAT (naming sudah). Hanya WHY non-obvious.
- ❌ Multi-line comment block kecuali public API non-trivial.
- ❌ "Just in case" feature flag untuk single-user.
- ❌ Abstraction yang dipakai 1×.
- ❌ Test yang mock lebih kompleks dari kode yang di-test.
- ❌ Premature performance optimization tanpa profile.
- ❌ Generated doc yang tidak dibaca.
- ❌ Error handling untuk skenario yang tidak bisa terjadi.
- ❌ Backwards-compat shim di codebase yang belum punya user.
- ❌ Rewrite file untuk perubahan satu baris.

### 4.4 Scope Discipline

**AI boleh:** summarize, explain, compare, question, critique plan, redact data privat sebelum kirim ke LLM.

**AI tidak boleh:**
- Bilang "buy/sell now", "guaranteed", "strong buy", "this is safe".
- Approve trade plan (schema tidak punya `approval` field).
- Memprediksi exact future price sebagai fakta.
- Auto-execute apa pun (no broker integration, no order placement).
- Generate output yang ditujukan ke "your audience" / "your clients".
- Menggeser scope ke multi-user, auth, billing, SaaS, copy trading, social trading.

Output AI wajib structured schema: `evidence` + `caveats` non-empty + `not_financial_advice: true`. Banned phrases di-filter regex. Detail: [`.docs/AI_BOUNDARIES.md`](.docs/AI_BOUNDARIES.md).

### 4.5 Communication

- Bahasa Indonesia default kecuali user switch.
- Jawaban pendek, langsung. Hindari preamble & summary di akhir tiap turn.
- Cite path dengan format `[file.ts:42](path/file.ts#L42)`.
- Saat ragu antara dua approach → pilih yang lebih mudah di-rollback, jelaskan trade-off 1 kalimat.
- Saat data tidak cukup → bilang "tidak tahu / data kurang", bukan tebak.
- Jangan klaim selesai sebelum lint + type check + test pass.

### 4.6 Contribution Identity

**Aturan kontribusi AI-assisted:**

- ❌ **Jangan** tambahkan `Co-Authored-By: Claude` (atau model AI lain) di commit message.
- ❌ **Jangan** tambahkan tag `🤖 Generated with [Claude Code]` di commit/PR body.
- ❌ **Jangan** push commit langsung dari AI dengan author identity AI; selalu pakai identity git owner repo.
- ❌ **Jangan** muncul sebagai contributor di GitHub graph (no bot account, no AI co-author).
- ✅ Author + committer di commit = **owner repo** (manusia).
- ✅ Kalau perlu menandai bahwa kode di-draft AI → catat di PR description atau changelog **dalam prosa**, bukan via trailer/metadata git.
- ✅ AI = ghostwriter, owner = author. Tanggung jawab penuh tetap di owner.

Alasan: repo publik, fokus sharing teknologi & ownership manusia. AI attribution di git metadata mengaburkan akuntabilitas dan mengotori GitHub contributor stats.

---

## 5. Repo Mental Model

```
apps/web/          Next.js 15 dashboard (TypeScript)
packages/core/     Python data core (framework-independent)
  ├─ data_sources  yfinance, RSS, IDX adapter
  ├─ indicators    MA, RSI, MACD, VWAP — pure functions, tested
  ├─ risk          position size, drawdown
  ├─ journal       trade plan & review
  ├─ ai            LLM wrapper + prompt + RAG context builder
  ├─ news          dedup + summarize
  └─ schemas       Pydantic + SQL migrations
packages/ui/       Shared TS components (IndicatorCard, FreshnessBadge, AIOutputPanel)
scripts/           Python CLI entrypoints (cron-callable)
data/sample/       Fake committed data
data/private/      GITIGNORED — real DB, journal, portfolio, logs
prompts/system/    LLM prompt templates (versioned, no private data)
config/            *.example.yml committed, *.yml gitignored
.docs/             Modular docs (lihat .docs/README.md)
```

---

*End of CLAUDE.md — detail teknis di `.docs/`.*
