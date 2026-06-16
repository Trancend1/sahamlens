# SahamLens — LLM Connectivity Audit & Execution Plan

> **Pemilik:** Product Architect
> **Tujuan:** Verifikasi koneksi LLM ke seluruh fitur, identifikasi gap env/config, dan rencana eksekusi perbaikan.
> **Status:** 🔴 3 Critical bugs + 2 Medium bugs ditemukan

---

## 1. Ringkasan Temuan

| # | Bug | Tingkat | Dampak | File |
|---|---|---|---|---|
| B1 | Env name mismatch: `.env.example` pakai `LLM_PROVIDER`, code baca `SAHAMLENS_LLM_PROVIDER` | 🔴 Critical | LLM tidak pernah terkoneksi — provider tidak terbaca | `.env.example`, `.env.local` |
| B2 | Env name mismatch: `.env.example` pakai `LLM_DEFAULT_MODEL`, code baca `SAHAMLENS_LLM_MODEL` | 🔴 Critical | Model tidak terbaca — fallback ke "" | `.env.example`, `.env.local` |
| B3 | `LLM_PROVIDER=tokenrouter` tidak ada di `_OPENAI_COMPAT_KINDS` | 🔴 Critical | `resolve_provider()` raise `ValueError` | `provider.py:41-43` |
| B4 | `SAHAMLENS_LLM_BASE_URL` tidak didokumentasi di `.env.example` | 🟡 Medium | User non-Anthropic tidak tahu harus isi apa | `.env.example` |
| B5 | `LLM_DAILY_COST_CAP_IDR` (IDR) tidak pernah dibaca — cost budget dari YAML (USD) | 🟡 Medium | Env mati/dokumentasi menyesatkan | `.env.example`, `router.py` |
| B5b | `ANTHROPIC_API_KEY` ada nilainya tapi provider bukan `anthropic` — key tidak pernah dipakai | 🟡 Medium | Key sia-sia, perlu `SAHAMLENS_LLM_API_KEY` | `.env.local` |

---

## 2. LLM Usage per Feature

### 2.1 Fitur yang **TIDAK** Butuh LLM

| Fitur | Module | Mekanisme |
|---|---|---|
| **Data Quality** | `packages/core/data_quality/` | Murni aggregasi DB — baca provider_health, source_coverage |
| **Screener** | `packages/core/screener/` | Evaluasi aturan lokal vs fundamental_snapshots |
| **Weekly Review** | `packages/core/journal/` | Aggregasi statistik jurnal |
| **Strategy Rules** | `packages/core/strategy/` | Named rule checks tanpa AI |
| **Alerts** | `packages/core/alerts/` | Threshold + lifecycle lokal |
| **Earnings** | `packages/core/earnings/` | Manual-first workflow |
| **Watchlist** | `packages/core/watchlist/` | CRUD daftar pantauan |
| **Portfolio** | `packages/core/portfolio/` | Posisi + harga lokal |
| **Indicators** | `packages/core/indicators/` | Kalkulasi numerik murni |

### 2.2 Fitur yang **Butuh** LLM

| Fitur | Orkestrator | Skema | API Route / CLI |
|---|---|---|---|
| **Stock Brief** | `ai/generate_brief.py` → `complete_json()` | `StockBrief` | `POST /api/stocks/[symbol]/brief`, `scripts.generate_brief brief` |
| **Stock Chat** | `ai/stock_chat.py` → `complete_json()` | `ChatResponse` | `POST /api/stocks/[symbol]/chat`, `scripts.generate_brief chat` |
| **Journal Critique** | `ai/critique_plan.py` → `complete_json()` | `JournalCritique` | `POST /api/journal/critique/[id]`, `scripts.journal plan critique` |
| **News Summary** | `ai/summarize_news.py` → `complete_json()` | `NewsSummary` | `scripts.summarize_news` |
| **Hermes Agent Brief** | `services/hermes/dispatch.py` → `generate_stock_brief` | `StockBrief` | `/brief` via Telegram |
| **Hermes Agent Ticker** | `services/hermes/dispatch.py` → `answer_stock_question` | `ChatResponse` | `/ticker` via Telegram |

---

## 3. Root Cause Analysis

### 3.1 Diagram Alir Koneksi LLM — Kondisi Sekarang

```
.env.local (milik user)
┌─────────────────────────────────┐
│ LLM_PROVIDER=tokenrouter         │ ← env name SALAH
│ LLM_DEFAULT_MODEL=MiniMax-M3     │ ← env name SALAH
│ ANTHROPIC_API_KEY=sk-PEiN...     │ ← API key (tapi provider bukan anthropic)
│ (tidak ada SAHAMLENS_LLM_BASE_URL)│ ← WAJIB untuk non-Anthropic
│ (tidak ada SAHAMLENS_LLM_API_KEY) │ ← WAJIB untuk non-Anthropic
└─────────────────────────────────┘
         │
         │ code baca:
         │ SAHAMLENS_LLM_PROVIDER → tidak ketemu → default "anthropic"
         │ SAHAMLENS_LLM_MODEL → tidak ketemu → ""
         │ SAHAMLENS_LLM_API_KEY → tidak ketemu → ""
         │
         ▼
┌─────────────────────────────────┐
│ resolve_provider()               │
│   kind = "anthropic" (default)   │
│   → return AnthropicProvider     │
│     api_key="" (tidak terisi)    │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ generate_stock_brief()           │
│   provider.complete_json()       │
│   → _send() → api_key=""         │
│   → return None (skip)           │
│   → Web: "AI brief tidak tersedia"│
└─────────────────────────────────┘
```

### 3.2 Env yang Seharusnya

```
Untuk tokenrouter → harus pakai OpenAICompatibleProvider:
┌────────────────────────────────────────────┐
│ SAHAMLENS_LLM_PROVIDER=openrouter           │
│ SAHAMLENS_LLM_BASE_URL=https://api.token... │
│ SAHAMLENS_LLM_API_KEY=sk-PEiN...            │
│ SAHAMLENS_LLM_MODEL=MiniMax-M3              │
└────────────────────────────────────────────┘

Atau jika tokenrouter ingin jadi provider resmi:
→ Tambah "tokenrouter" ke _OPENAI_COMPAT_KINDS di provider.py:41
```

---

## 4. Execution Plan

### 4.1 Task Breakdown

| ID | Task | File | Effort | Priority |
|---|---|---|---|---|
| **L1** | Fix `.env.example` — rename `LLM_PROVIDER` → `SAHAMLENS_LLM_PROVIDER` | `.env.example` | 5 menit | 🔴 P0 |
| **L2** | Fix `.env.example` — rename `LLM_DEFAULT_MODEL` → `SAHAMLENS_LLM_MODEL` | `.env.example` | 5 menit | 🔴 P0 |
| **L3** | Fix `.env.example` — tambah `SAHAMLENS_LLM_BASE_URL` dengan komentar | `.env.example` | 5 menit | 🔴 P0 |
| **L4** | Fix `.env.example` — tambah `SAHAMLENS_LLM_API_KEY` dengan komentar | `.env.example` | 5 menit | 🔴 P0 |
| **L5** | Fix `.env.example` — ganti contoh `tokenrouter` → `openrouter` (atau `custom`) | `.env.example` | 5 menit | 🔴 P0 |
| **L6** | Fix `.env.example` — hapus `LLM_DAILY_COST_CAP_IDR` atau ganti jadi `LLM_DAILY_COST_CAP_USD` dengan referensi ke `config/cost_budget.yml` | `.env.example` | 10 menit | 🟡 P1 |
| **L7** | Opsional: tambah `"tokenrouter"` ke `_OPENAI_COMPAT_KINDS` untuk dukung value user | `provider.py:41` | 2 menit | 🟡 P1 |
| **L8** | Fix `.env.local` user — sesuaikan nama env + tambah BASE_URL + API_KEY | `.env.local` | 2 menit | 🔴 P0 |
| **L9** | Verifikasi: `uv run python -m scripts.generate_brief brief --symbol BBCA.JK` setelah fix | CLI | 5 menit | 🔴 P0 |
| **L10** | Verifikasi: test provider multi-environment | `pytest packages/core/ai/test_provider_multi.py` | 2 menit | 🟡 P1 |
| **L11** | Cek apakah Hermes config juga kena masalah env name yang sama | `services/hermes/config.py:19` | 5 menit | 🟢 P2 |

### 4.2 Prioritas Eksekusi

```
Segera (hari ini):
  L1 + L2 + L3 + L4 + L5 + L8 + L9 = ~20 menit

Minggu ini:
  L6 + L7 + L10 = ~20 menit

Nice-to-have:
  L11 = ~5 menit
```

### 4.3 File yang Diubah

| File | Perubahan |
|---|---|
| `.env.example` | 6 baris env — rename + tambah + hapus |
| `.env.local` | Sesuaikan dengan env name yang benar |
| `packages/core/ai/provider.py` | Opsional: +1 line `"tokenrouter"` |
| `.docs/plan/audit-llm.md` | Dokumen ini |

### 4.4 Definition of Done

- [ ] `.env.example` sudah pakai prefix `SAHAMLENS_LLM_*` yang konsisten
- [ ] `SAHAMLENS_LLM_BASE_URL` dan `SAHAMLENS_LLM_API_KEY` tercantum
- [ ] Provider name di example menggunakan value yang didukung code
- [ ] `LLM_DAILY_COST_CAP_IDR` dihapus atau diganti jadi referensi ke YAML config
- [ ] `uv run python -m scripts.generate_brief brief --symbol BBCA.JK` menghasilkan StockBrief (bukan None)
- [ ] Test provider multi-environment pass

---

## 5. Env Mapping (Final — Target)

| .env.local | Code reads | Wajib? | Untuk |
|---|---|---|---|
| `SAHAMLENS_LLM_PROVIDER=openrouter` | `provider.py:35` ✅ | Ya | Seleksi provider |
| `SAHAMLENS_LLM_BASE_URL=https://api.tokenrouter.io/v1` | `provider.py:36` ✅ | Ya (non-Anthropic) | Base URL API |
| `SAHAMLENS_LLM_API_KEY=sk-xxx...` | `provider.py:37` ✅ | Ya (non-Anthropic) | API key |
| `SAHAMLENS_LLM_MODEL=MiniMax-M3` | `provider.py:38` ✅ | Ya (non-Anthropic) | Nama model |
| `ANTHROPIC_API_KEY=sk-ant-xxx...` | `provider.py:39` ✅ | Hanya untuk Anthropic | API key Anthropic |
| `DUCKDB_PATH=./data/private/sahamlens.duckdb` | `repository.py:19` ✅ | Tidak (punya default) | Path DB |
| `SAHAMLENS_TELEGRAM_BOT_TOKEN=...` | `hermes/config.py:17` | Optional | Telegram |
| `SAHAMLENS_TELEGRAM_CHAT_ID=...` | `hermes/config.py:18` | Optional | Telegram |
| `PYTHON_BIN=...` | `pythonRunner.ts:263` | Tidak (auto-detect) | Python path |

---

## 6. Catatan Tambahan

- **Cost budget** tidak pakai env var — lihat `config/cost_budget.yml` atau `config/cost_budget.example.yml`
- **Hermes runtime** (`services/hermes/config.py:19`) juga pakai `SAHAMLENS_LLM_PROVIDER` — konsisten dengan provider.py
- **Validator** (`ai/validator.py`) akan tetap memfilter banned phrases — tidak terkait env
- **8 dari 12 fitur** user tetap berfungsi tanpa LLM — hanya stock brief, stock chat, journal critique, dan news summary yang terpengaruh
