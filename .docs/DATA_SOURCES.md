# DATA_SOURCES — SahamLens

**Source of truth for:** Daftar source data, reliability, rate limits, fallback strategy, freshness policy, canonical ticker format, forbidden data practices (operational level).
**Tidak di sini:** Schema penyimpanan (→ [ARCHITECTURE.md §6](ARCHITECTURE.md)), aturan repo public soal data (→ [SECURITY.md](SECURITY.md)), AI-side handling source (→ [AI_BOUNDARIES.md](AI_BOUNDARIES.md)).

**Versi:** 1.0
**Status:** Active

---

## 1. Source Catalog

### 1.1 MVP

| Data Type | Source | Endpoint / Library | Tier | Notes |
|---|---|---|---|---|
| OHLCV harian | yfinance | `yfinance` Python lib, ticker `<KODE>.JK` | Free | Tidak sempurna; cukup untuk EOD belajar |
| Fundamental dasar | yfinance (`Ticker.info`) | sama | Free | Availability per ticker bervariasi — validasi sebelum trust |
| Fundamental fallback | IDX public files | https://www.idx.co.id/ (manual / scheduled download) | Free | Untuk emiten yang yfinance kosong |
| News | RSS publik | Detik Finance, CNBC Indonesia, Kontan | Free | Simpan url + title + timestamp + source. Tidak scrape full content kecuali ToS izinkan |
| Portfolio | Manual entry / CSV export Stockbit | UI form / file upload | Local | **Tidak ada broker login** ([ADR-0004](adr/ADR-0004-no-broker-credential.md)) |
| Journal | Local DB | DuckDB `journal` table | Local | Privat ([SECURITY.md](SECURITY.md)) |
| Strategy rule | Local YAML | `config/*.yml` (gitignored selain `.example`) | Local | Template versioned, nilai privat di-ignore |

### 1.2 V1+ (planned)

| Data Type | Source | Catatan |
|---|---|---|
| IDX corporate actions | IDX announcements page | Manual / scheduled fetch |
| Sector / industry mapping | IDX + manual mapping table | One-time seed, update kuartal |
| Intraday delayed | TBD (yfinance limited, mungkin paid) | Evaluate kalau swing trading butuh |
| Earnings reports | IDX filings PDF | Manual upload + AI summarizer |

### 1.3 Experimental (terisolasi, V2+)

Social sentiment (Twitter/X, Stockbit stream) — **noisy + ToS risk**. Kalau dibangun: opt-in, terpisah dari decision support, label experimental. Lihat [PRD_clean.md §5.3](PRD_clean.md).

---

## 2. Canonical Ticker Format

- Format internal: `<KODE>.JK` (uppercase + suffix `.JK`).
- Adapter wajib normalize sebelum query DB.
- Validasi: 4 huruf alfanumerik + `.JK`. Reject input yang tidak match.

```python
# packages/core/data_sources/normalize.py
import re
TICKER_RE = re.compile(r"^[A-Z0-9]{4}\.JK$")

def normalize_ticker(raw: str) -> str:
    cleaned = raw.strip().upper()
    if not cleaned.endswith(".JK"):
        cleaned += ".JK"
    if not TICKER_RE.match(cleaned):
        raise ValueError(f"Invalid IDX ticker: {raw}")
    return cleaned
```

---

## 3. Reliability Requirements (Per Record)

Setiap record yang ter-persist **wajib** track:

| Field | Wajib | Catatan |
|---|---|---|
| `source` | ✅ | Identifier source (e.g. `yfinance`, `idx_public`, `manual`) |
| `fetched_at` | ✅ | ISO 8601 UTC, waktu fetch sukses |
| `market_date` | ✅ untuk OHLCV/fundamental | Tanggal pasar (bukan fetch) |
| `symbol` | ✅ | Canonical format |
| `derivation` | ✅ untuk indicator/AI | `raw` / `calculated` / `ai_derived` |
| `fetch_status` | ✅ untuk attempted fetch | `ok` / `partial` / `failed` |
| `error_message` | kalau failed | Untuk debugging, tidak ditampilkan ke user |

Akibat: tidak ada query yang mengembalikan data tanpa metadata freshness. UI selalu bisa render `<FreshnessBadge />`.

---

## 4. Rate Limits & Politeness

| Source | Rate Limit (defensif) | Strategy |
|---|---|---|
| yfinance | 1 request / 0.5 detik per ticker | Sequential dengan delay; backoff exponential 1→2→4→8s saat 429 |
| RSS news | 1 fetch / source / 10 menit | Cron-driven; cache ETag/Last-Modified |
| IDX public | 1 request / 2 detik | Manual + scheduled, jangan paralel besar |

**Global rules:**
- Tidak ada concurrent request > 4 ke satu host.
- User-Agent header eksplisit: `SahamLens/1.0 (personal use; +contact-email-if-needed)`.
- Hormati `robots.txt` & ToS. Kalau ragu, dokumentasikan keputusan di `.docs/notes/sources/<source>.md`.

---

## 5. Caching Strategy

| Layer | TTL | Storage |
|---|---|---|
| OHLCV harian (EOD) | Sampai market close berikutnya | DuckDB `price_history` |
| Fundamental | 7 hari (data perubahan jarang) | DuckDB `stocks` + fundamental column |
| Indicator hasil calc | Recompute on price update | DuckDB `indicator_cache` |
| News RSS | 10 menit | DuckDB `news` (dedup by URL UNIQUE) |
| LLM summary news | Permanent (per news_id) | `news.summary` column |
| LLM brief / chat | Tidak di-cache (context dinamis) | `ai_log` untuk audit only |

Invalidation: cron job `scripts/refresh_cache.py` (V1) — flush expired rows; sampai sebelumnya, freshness check di read time.

---

## 6. Fallback Strategy

```
[fetch price BBCA.JK]
  primary: yfinance
  on failure (429 / 5xx / parse error):
    log error → fetch_status='failed'
    try secondary: IDX public file (kalau tersedia)
    on still-failed:
      mark stale, do NOT silently substitute
      UI FreshnessBadge → red, CTA trade-plan disabled
```

**Anti-pattern:** silent substitution dari source berbeda tanpa user tahu. Selalu surface kegagalan.

Multi-source adapter di `packages/core/data_sources/<source>/`. Interface seragam:
```python
class PriceSource(Protocol):
    name: str
    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> FetchResult: ...
```

---

## 7. Schema Drift Handling

Source eksternal bisa ubah field tanpa notice. Mitigasi:
1. **Schema validation** di adapter (Pydantic) — reject unexpected shape, log to `data/private/logs/schema_drift.log`.
2. **Snapshot test** mingguan: fetch 1 ticker reference, compare shape vs golden file. Kalau berubah → manual review.
3. **No silent coercion** — kalau field tipe berubah, surface error daripada force-cast.

---

## 8. Cost Tracking (LLM-Affected)

Sumber data yang trigger LLM call (news summarization, brief generation) di-track per call. Lihat [ARCHITECTURE.md §11](ARCHITECTURE.md). Cap harian dari `config/cost_budget.yml`. Saat cap tercapai: skip LLM step, simpan raw data + flag `pending_summary=true`.

---

## 9. Forbidden Data Practices

Diulang dari [SECURITY.md](SECURITY.md) untuk konteks operasional:

- ❌ Commit data portofolio ke GitHub.
- ❌ Simpan password / cookie broker.
- ❌ Bypass platform protection (CAPTCHA, anti-bot).
- ❌ Representasikan data scraped sebagai resmi.
- ❌ Buat keputusan trading saat freshness data tidak diketahui.
- ❌ Aggressive scraping (>1 req/detik ke satu host, ignore robots.txt).
- ❌ Re-publish full content news yang berhak cipta (cuma link + ringkasan singkat AI).

---

## 10. Adding a New Source — Checklist

1. Buat ADR singkat kalau source punya implikasi besar (cost, ToS, dep).
2. Implement adapter di `packages/core/data_sources/<source>/`.
3. Schema validation (Pydantic).
4. Update tabel §1.
5. Update rate limit §4.
6. Tambah test fixture + golden file.
7. Update `.env.example` kalau butuh API key baru.
8. Update `config/*.example.yml` kalau ada knob baru.
9. Dokumentasi singkat di `.docs/notes/sources/<source>.md` (ToS link, reliability anecdote).
