# ARCHITECTURE — SahamLens

**Source of truth for:** System design, module boundaries, data flow, tech stack, infrastructure, deployment, storage, schema.
**Tidak di sini:** Product scope (→ [PRD_clean.md](PRD_clean.md)), AI rules (→ [AI_BOUNDARIES.md](AI_BOUNDARIES.md)), data source catalog (→ [DATA_SOURCES.md](DATA_SOURCES.md)), security controls (→ [SECURITY.md](SECURITY.md)), code style (→ [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md)).

**Versi:** 1.0
**Status:** Active

---

## 1. Architecture Philosophy

1. **Local-first.** Default execution & storage di mesin owner. Cloud opsional, opt-in per fitur. (→ [ADR-001](adr/ADR-0001-local-first.md))
2. **Single boundary per concern.** Satu UI server, satu data engine, satu LLM wrapper. Tidak ada microservice sebelum bottleneck nyata.
3. **Framework-independent data core.** Logika finansial murni Python, bisa hidup tanpa UI.
4. **Cron-driven ingestion.** Tidak ada always-on worker. Job berhenti setelah selesai.
5. **Explainable.** Setiap output ke owner punya source + freshness + caveat.

---

## 2. System Blueprint (MVP)

```
┌────────────────────────────────────────────────────────────────┐
│  Public Data Sources                                           │
│  yfinance .JK  •  IDX OpenData  •  RSS news (Detik/CNBC/Kontan)│
└──────────────────────────────┬─────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────┐
│  Scheduled Local Ingestion (cron + Python CLI scripts)         │
│  scripts/ingest_prices.py · ingest_news.py · calc_indicators.py│
│  - retry + rate limit + schema validation                      │
└──────────────────────────────┬─────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────┐
│  DuckDB (single local file, data/private/sahamlens.duckdb)     │
│  schema dikelola via migration files                           │
└──────────────────────────────┬─────────────────────────────────┘
                               │
       ┌─────────────┬─────────┼──────────┬──────────────┐
       ▼             ▼         ▼          ▼              ▼
  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
  │Indicator │ │ News     │ │Journal │ │ Risk   │ │ AI Context   │
  │ engine   │ │summarizer│ │ engine │ │ engine │ │ builder      │
  └─────┬────┘ └────┬─────┘ └───┬────┘ └────┬───┘ └──────┬───────┘
        └───────────┴───────────┼───────────┴────────────┘
                                ▼
                ┌───────────────────────────────────┐
                │  Next.js 15 dashboard             │
                │  App Router · shadcn/ui · Tailwind│
                │  API routes hit data core via:    │
                │   (a) DuckDB direct (read)        │
                │   (b) Python CLI exec (heavy ops) │
                └───────────────┬───────────────────┘
                                ▼
                ┌───────────────────────────────────┐
                │  Owner decision + journal write   │
                └───────────────────────────────────┘
```

Cloud boundary (opsional):
- LLM API (Anthropic), Telegram Bot API, Vercel hosting privat (tanpa data portofolio), GitHub Actions (lint/test).

---

## 3. Tech Stack

| Layer | Pilihan | ADR |
|---|---|---|
| UI framework | Next.js 15 (App Router) + TypeScript strict | [ADR-0003](adr/ADR-0003-ui-framework.md) |
| Styling | Tailwind CSS + shadcn/ui | [ADR-0003](adr/ADR-0003-ui-framework.md) |
| Charts | lightweight-charts atau Recharts | — |
| Backend boundary | Next.js API routes (TypeScript) untuk user-facing; Python CLI untuk heavy ops | [ADR-0008](adr/ADR-0008-python-core-via-cli.md) |
| Data core | Python 3.11+ · pandas · pandas-ta (atau formula custom) | — |
| Database | DuckDB (single file) | [ADR-0002](adr/ADR-0002-database-duckdb.md) |
| LLM | Provider wrapper (default Claude) | [ADR-0005](adr/ADR-0005-llm-wrapper.md) |
| Job runner | Cron lokal (atau Windows Task Scheduler) memanggil CLI | — |
| Secrets | `.env.local` (gitignored) | → [SECURITY.md](SECURITY.md) |
| Testing | Vitest (TS) · pytest (Python) | → [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) |

---

## 4. Module Boundaries

| Module | Tugas | Tidak Boleh |
|---|---|---|
| `packages/core/data_sources` | Fetch & normalize public data | Interpret trade |
| `packages/core/indicators` | Hitung formula | Generate advice |
| `packages/core/news` | Dedup + summarize via LLM wrapper | Klaim kausalitas pasti |
| `packages/core/ai` | LLM wrapper + prompt templates + RAG | Decide buy/sell (→ [AI_BOUNDARIES.md](AI_BOUNDARIES.md)) |
| `packages/core/journal` | Persist trade plan & review | Auto-edit history |
| `packages/core/risk` | Position size + checklist | Override decision user |
| `apps/web` | Render state | Sembunyikan freshness; ekspos heavy compute ke browser |
| `scripts/*` | Cron-executable Python entrypoint | Mengandung business logic (cuma orchestration) |

Inter-module rule: dependency satu arah (`apps/web → packages/core/*`). Tidak ada module di `packages/core/*` boleh import dari `apps/web`.

---

## 5. Data Flow Examples

### 5.1 Morning Brief Generation
```
[cron 07:00 WIB]
  → scripts/ingest_prices.py        (yfinance → DuckDB.price_history)
  → scripts/ingest_news.py          (RSS → DuckDB.news, AI summarize → news.summary)
  → scripts/calculate_indicators.py (DuckDB.price_history → indicator_cache)
[cron 07:30 WIB]
  → scripts/generate_brief.py       (DuckDB read → LLM wrapper → write brief artifact)
[user opens dashboard]
  → Next.js page reads brief artifact + watchlist + freshness badges
```

### 5.2 Pre-Trade Plan Submit
```
[user opens stock detail → "New Trade Plan"]
  → Next.js form (zod validation)
  → POST /api/journal/plan
  → API route calls packages/core/journal + packages/core/risk
  → DuckDB.journal INSERT (status='planned')
  → (optional) LLM critique via packages/core/ai
  → Render critique + caveat to user
```

---

## 6. Database Schema (MVP)

File DB privat: `data/private/sahamlens.duckdb` (gitignored, lihat [SECURITY.md](SECURITY.md)). Tidak ada `users` table — single-user.

```sql
-- Master data
CREATE TABLE stocks (
  symbol TEXT PRIMARY KEY,         -- 'BBCA.JK'
  name TEXT NOT NULL,
  sector TEXT,
  industry TEXT,
  is_active INTEGER DEFAULT 1
);

CREATE TABLE price_history (
  symbol TEXT NOT NULL,
  date TEXT NOT NULL,
  open REAL, high REAL, low REAL, close REAL,
  volume BIGINT,
  source TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  PRIMARY KEY (symbol, date)
);

CREATE TABLE watchlist (
  symbol TEXT PRIMARY KEY,
  tag TEXT,
  note TEXT,
  added_at TEXT NOT NULL
);

-- PRIVATE — never committed
CREATE TABLE journal (
  id BIGINT PRIMARY KEY,
  symbol TEXT,
  setup_type TEXT,
  thesis TEXT,
  entry_plan TEXT,
  stop_level REAL,
  invalidation TEXT,
  target TEXT,
  position_size_rupiah BIGINT,
  max_loss_rupiah BIGINT,
  emotion TEXT,
  status TEXT,                     -- 'planned'|'open'|'closed'|'skipped'
  result_rupiah BIGINT,
  lesson TEXT,
  created_at TEXT NOT NULL,
  reviewed_at TEXT
);

-- PRIVATE
CREATE TABLE portfolio_position (
  symbol TEXT,
  lots INTEGER,
  avg_price REAL,
  imported_at TEXT,
  source TEXT,                     -- 'manual'|'csv'
  PRIMARY KEY (symbol, imported_at)
);

CREATE TABLE news (
  id BIGINT PRIMARY KEY,
  url TEXT UNIQUE,
  title TEXT,
  source TEXT,
  published_at TEXT,
  summary TEXT,                    -- AI generated
  affected_tickers TEXT,           -- comma-separated
  sentiment_label TEXT,            -- 'bullish'|'neutral'|'bearish'|'mixed'
  fetched_at TEXT
);

CREATE TABLE ai_log (
  id BIGINT PRIMARY KEY,
  prompt_template_id TEXT,
  model TEXT,
  input_context TEXT,
  output TEXT,
  confidence REAL,
  caveats_count INTEGER,
  created_at TEXT
);

CREATE TABLE indicator_cache (
  symbol TEXT,
  date TEXT,
  indicator TEXT,                  -- 'ma_5','rsi_14','macd_signal'...
  value REAL,
  PRIMARY KEY (symbol, date, indicator)
);
```

**Migration strategy:** plain SQL files di `packages/core/schemas/migrations/NNNN_description.sql`, applied in order. Tooling: simple Python migrator script (avoid Alembic-grade complexity sampai dibutuhkan).

---

## 7. Risk Engine — Position Sizing Formula

```
risk_rupiah   = portfolio_value × risk_percent
risk_per_lot  = (entry_price - stop_price) × 100   # 1 lot = 100 lembar IDX
max_lots      = floor(risk_rupiah / risk_per_lot)
```

Implementasi di `packages/core/risk/position_size.py`. Coverage requirement: ≥ 90% dengan edge case (stop di atas entry untuk short, stop = entry, fractional lots, dll). Lihat [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md).

---

## 8. Storage Decisions

**MVP:** DuckDB single-file. Justifikasi: analytical query (OHLCV scan, indicator rolling window) lebih cepat dari SQLite OLTP-style, single-file portability sama. ([ADR-0002](adr/ADR-0002-database-duckdb.md))

**PostgreSQL hanya saat:**
- Data model stabil ≥ 3 bulan.
- App di-deploy multi-machine.
- Concurrent write jadi bottleneck nyata.

**Hindari di MVP:** Redis, TimescaleDB, Kafka, Kubernetes, Vector DB. Full-text search via DuckDB native (atau SQLite FTS5 kalau migrasi).

---

## 9. LLM Routing

Provider wrapper di `packages/core/ai/provider.py` — bisa swap model tanpa ubah business logic. Default routing:

| Task | Model | Alasan |
|---|---|---|
| News summarization (bulk) | Claude Haiku | Murah, cepat |
| Daily brief, indicator explanation | Claude Sonnet | Balanced |
| Deep earnings analysis (jarang) | Claude Opus | Reasoning kuat |
| Journal pattern recognition | Claude Sonnet | Balanced |

Routing rule + circuit breaker (cost cap per hari) di `packages/core/ai/router.py`. ([ADR-0005](adr/ADR-0005-llm-wrapper.md))

---

## 10. Deployment Topology

### Default (MVP)
Everything lokal. `pnpm dev` untuk Next.js, cron OS-native untuk ingestion. Tidak ada cloud component selain LLM API.

### Optional (V1+)
- **Hosted dashboard privat** di Vercel — DB tetap lokal, dashboard read via secure tunnel (tailscale / cloudflared). Tidak commit data portofolio.
- **Telegram notification** via bot lokal yang membaca DuckDB.
- **GitHub Actions** untuk lint/test/security scan (tidak deploy data).

Tidak ada plan multi-region, load balancer, atau auto-scaling untuk MVP/V1.

---

## 11. Observability (Minimal)

- **Logs:** struktur per modul, file-rotating di `data/private/logs/`. Tidak boleh log data portofolio (lihat [SECURITY.md](SECURITY.md)).
- **AI audit log:** `ai_log` table — input, prompt_template_id, model, output, confidence, caveats_count.
- **Cost tracking:** counter LLM token usage harian, cap dari config.
- **Data freshness:** per-table `fetched_at` jadi sumber tunggal untuk freshness badge di UI.

Tidak ada Prometheus/Grafana/Sentry di MVP. Tambahkan kalau ada bug yang sulit di-reproduce lokal.

---

## 12. Architecture Decision Records

| ADR | Topik |
|---|---|
| [0001](adr/ADR-0001-local-first.md) | Local-first architecture |
| [0002](adr/ADR-0002-database-duckdb.md) | DuckDB sebagai DB MVP |
| [0003](adr/ADR-0003-ui-framework.md) | Next.js 15 + shadcn/ui |
| [0004](adr/ADR-0004-no-broker-credential.md) | Tidak ada broker credential storage |
| [0005](adr/ADR-0005-llm-wrapper.md) | LLM provider wrapper |
| [0006](adr/ADR-0006-no-predictive-mvp.md) | Tidak ada predictive AI di MVP |
| [0007](adr/ADR-0007-doc-language.md) | Bahasa Indonesia primary untuk dokumentasi |
| [0008](adr/ADR-0008-python-core-via-cli.md) | Python core diekspos via CLI scripts, bukan separate HTTP service |
