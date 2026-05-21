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
**Sprint aktif:** **S7 — Freshness UX + polish + portfolio import**.

**S2 deliverable (done ✓):**
- `packages/core/indicators/formulas.py` — pure `sma`, `ema`, `rsi_wilder` (Wilder smoothing, SMA seed), `macd` (12/26/9). Pandas-only, no extra dep.
- `packages/core/indicators/engine.py` — `compute_all(symbol, prices_df) → list[IndicatorPoint]` (10 keys: MA 5/10/15/50/200, vol_avg_20, rsi_14, macd_line/signal/hist).
- `packages/core/indicators/repo.py` — `upsert_indicator_points`, `load_price_series`, `latest_for`.
- `packages/core/schemas/models.py` — `IndicatorPoint` Pydantic model.
- `scripts/calculate_indicators.py` CLI (mirror `ingest_prices.py`; full history recompute, idempotent).
- Tests: golden (Wilder 1978 RSI sample) + Hypothesis property tests + engine + repo + CLI smoke (37 tests, indicator coverage 98%).
- CI gate: `--cov-fail-under=90` untuk `packages/core/indicators`.

**S3 deliverable (done ✓):**
- `packages/core/schemas/repository.py` — `load_ohlcv(conn, symbol, limit=N)` returns OHLCVRow list (sorted ASC).
- `scripts/dump_stock_detail.py` — single-call CLI: `{ohlcv, indicators_series, indicators_latest, first_date, last_date}` JSON; exit 0/2/3.
- `apps/web/src/lib/indicatorMeta.ts` — 10-entry typed dictionary: label / category / whatItMeasures / falseSignal / horizonNote / interpret(value, ctx) / formatValue. Threshold-aware interpretation untuk RSI/MACD; harga-vs-MA delta-percent untuk MA.
- `apps/web/src/components/IndicatorCard.tsx` — 5-block presentational (PRD §9.2): label+badge, formatted value (`tabular-nums`), interpretasi, false signal, time horizon.
- `apps/web/src/components/StockChart.tsx` — 3-pane `lightweight-charts` v5: candle + MA 5/10/15/50/200 overlay, RSI 14 + 30/70 reference lines, MACD line/signal/histogram. Pane time-scales synced via `subscribeVisibleLogicalRangeChange`.
- `apps/web/src/lib/stockDetail.ts` — typed `runPython("scripts.dump_stock_detail", …)` wrapper (timeout 30s).
- `apps/web/src/app/stocks/[symbol]/page.tsx` — server component (`dynamic = "force-dynamic"`), header / chart / 10 IndicatorCards grid / disclaimer footer.
- `apps/web/src/app/watchlist/page.tsx` — ticker rows now linked to `/stocks/<short>`.
- Tests: 5 IndicatorCard + 10 indicatorMeta + 4 dump_stock_detail CLI + 5 load_ohlcv repository → 80 Python + 23 TS tests pass.

**S4 deliverable (done ✓):**
- `packages/core/news/` — `NewsArticle` / `NewsSummary` / `FetchNewsResult` Pydantic models, canonical URL + sha1-derived `article_id` dedup, `RSSNewsSource` adapter (stdlib `urllib` + `feedparser`, exponential backoff on 429, never raises), `repo` with idempotent upsert + ticker-filtered recent loader + `ai_log` audit writer, `pipeline.ingest_news` / `pipeline.summarize_pending`.
- `packages/core/ai/` — `LLMProvider` Protocol + `AnthropicProvider` (stdlib `urllib`, no third-party SDK, `tool_use` structured output, retries on 429/5xx), `ModelRouter` (Haiku for news, Sonnet for brief), `CircuitBreaker` (per-day cap from `ai_log` × cost table), versioned `PromptTemplate` loader, `validator` (banned-phrase regex + Pydantic + ≤3-kalimat invariant), `summarize_news` orchestrator (LLM∩regex ticker intersection, confidence downweight, 3× banned-phrase retry, never raises).
- Migration `0002_news_summary_fields.sql` adds `source_quality`, `confidence`, `caveats` (JSON), `prompt_template_id`, `model`, `summarized_at` + indexes ke tabel `news`.
- CLI: `scripts/ingest_news.py`, `scripts/summarize_news.py` (`--dry-run`, `--from-watchlist`), `scripts/dump_stock_detail.py` extended with `news_recent`.
- Web: `apps/web/src/lib/dateTime.ts` (Intl.RelativeTimeFormat id-ID + freshness tier), `FreshnessBadge`, `NewsCard` (sentiment badge, low-confidence banner <0.6, caveats, source quality, outbound link), `NewsSection` (server component, empty state, grid) inserted antara `<StockChart>` dan indicator grid.
- Config: `config/rss_feeds.example.yml` + `config/cost_budget.example.yml` (real files gitignored). Prompt `prompts/system/news_summary.v1.md` (Bahasa Indonesia, ≤3 kalimat, banned-phrase reinforcement, `not_financial_advice: true`).
- Tests: 30 news + 33 ai (Python) + 13 web (vitest). Coverage news 95%, ai 94% (gate ≥70%).
- Deps: `feedparser>=6.0.11`, `pyyaml>=6.0.2`. No `anthropic` SDK — stdlib `urllib` per scope decision.

**S5 deliverable (done ✓):**
- `packages/core/risk/calculator.py` — `position_size()` pure function (IDX formula: risk_rupiah / risk_per_lot, 1 lot = 100 shares). `PositionSizeResult` frozen dataclass.
- `packages/core/journal/models.py` — `TradePlan`, `JournalCritique`, `CritiqueCheck` Pydantic models (PRD §8.2). Schema tidak punya `approval` field by design.
- `packages/core/journal/repo.py` — `create_plan`, `load_plan`, `list_plans`, `update_status`. ID: microsecond epoch.
- `packages/core/ai/critique_plan.py` — `critique_trade_plan` orchestrator: budget check → render → complete_json → validate → log.
- `scripts/journal.py` — CLI: `plan add/list/get/update/critique`.
- Web: `TradePlanForm.tsx` (live position size calc via pure TS), `CritiquePanel.tsx`, `/journal` list page, `/journal/new` form page, API routes `/api/journal/plan` + `/api/journal/critique/[id]`.
- Prompt: `prompts/system/journal_critique.v1.md`.
- Tests: 222 Python pass. Risk coverage 100% (gate ≥90% ✓). Journal coverage 99% (gate ≥70% ✓).

**S6 deliverable (done ✓):**
- `packages/core/ai/models.py` — `EvidenceItem`, `StockBrief` (analysis_output schema AI_BOUNDARIES §3.1), `ChatResponse`.
- `packages/core/ai/context_builder.py` — `build_stock_context`: assembles price + indicators + news + journal dari DuckDB sebelum LLM call (RAG-first per AI_BOUNDARIES §4.1).
- `packages/core/ai/generate_brief.py` — `generate_stock_brief`: context build → prompt render → complete_json (max 1500 tokens) → validate → log. 3× retry on banned-phrase.
- `packages/core/ai/stock_chat.py` — `answer_stock_question`: single-turn RAG Q&A scoped ke satu saham.
- `packages/core/ai/validator.py` — tambah `validate_stock_brief` + `validate_chat_response`.
- `packages/core/ai/router.py` — tambah `stock_chat` task → Sonnet 4.6.
- `scripts/generate_brief.py` — CLI: `brief --symbol` + `chat --symbol --question`.
- Web: `StockBriefPanel.tsx` (lazy generate, bullish/bearish/uncertainty display), `ChatPanel.tsx` (client-side history, expandable evidence), API routes `/api/stocks/[symbol]/brief` + `/api/stocks/[symbol]/chat`. Stock detail page diperbarui.
- Prompts: `prompts/system/stock_brief.v1.md` + `stock_chat.v1.md`.
- Tests: 222 Python pass. AI coverage 95% (gate ≥70% ✓). tsc + eslint + mypy + ruff clean.

**Next:** S7 — Freshness UX + polish + portfolio import.

### 2.4 Exit Criteria

Phase MVP exit (semua wajib — sumber [`.docs/EXECUTION_BLUEPRINT.md §4.2`](.docs/EXECUTION_BLUEPRINT.md)):

Produk:
- [ ] Owner bisa review watchlist dalam 15–30 menit.
- [ ] Owner bisa buat trade plan lengkap (semua field PRD §8.2).
- [ ] AI output selalu cite data + tampilkan caveat.

Teknis:
- [ ] Tidak ada private data ter-commit (verified pre-commit + CI `no_private_leak`).
- [x] Core indicator calc test coverage ≥ 90%.
- [x] Position size calculator: ≥ 5 unit test + property-based.
- [x] Banned-phrase filter aktif di AI pipeline.
- [x] Schema validation reject malformed AI output.

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
