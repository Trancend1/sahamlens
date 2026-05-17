# AI_BOUNDARIES — SahamLens

**Source of truth for:** Apa AI boleh & tidak boleh, output schema, hallucination prevention, prompt strategy, confidence handling, audit log requirement, banned phrases.
**Tidak di sini:** Implementasi LLM wrapper (→ [ARCHITECTURE.md §9](ARCHITECTURE.md)), UI display (→ [DESIGN_SYSTEM.md §6.3](DESIGN_SYSTEM.md)), legal positioning (→ [TRADING_DISCLAIMER.md](TRADING_DISCLAIMER.md)).

**Versi:** 1.0
**Status:** Active — **governance, mengikat semua fitur AI**

---

## 1. Core Principle

> AI menjelaskan, user memutuskan.

AI di SahamLens adalah **co-pilot pendidikan**, bukan oracle. Setiap output AI yang user-facing tunduk pada aturan di dokumen ini. Tidak ada exception "kecuali user explicit minta" — owner sendiri pun terikat aturan ini karena tujuannya melindungi disiplin.

---

## 2. AI Capability Matrix

### 2.1 BOLEH

- Meringkas berita (dengan source + freshness).
- Menjelaskan indikator (apa, cara baca, false signal).
- Menerjemahkan jargon pasar ke bahasa pemula.
- Membandingkan ticker dengan kondisinya kemarin / minggu lalu.
- Menyorot evidence yang konflik (bullish vs bearish data sama-sama hadir).
- Mengajukan pertanyaan untuk dipertimbangkan owner.
- Meringkas pola journal (rule violation, repeated mistake).
- Mengubah note mentah jadi journal entry terstruktur.
- Menjelaskan rasio fundamental.
- Menyarankan topik belajar.
- Menandai data yang hilang / basi.
- Menghasilkan scenario analysis (bullish / base / bearish) **dengan caveat eksplisit**.
- Mengkritisi pre-trade plan (cari risk yang tidak disebut, invalidation lemah, position oversized).

### 2.2 TIDAK BOLEH

- Mengatakan *"buy this stock now"* / *"sell this stock now"*.
- Menjanjikan profit.
- Memprediksi exact future price sebagai fakta.
- Mengeksekusi trade / place order.
- Override risk rule yang user-defined.
- Menyembunyikan ketidakpastian.
- Menghasilkan advice untuk orang lain (LLM dilarang generate output yang ditujukan ke "your audience" / "your clients").
- Menggunakan data portofolio privat dalam contoh publik (lihat [SECURITY.md](SECURITY.md)).
- Scrape data broker terotentikasi.
- Menyetujui (approve) trade plan. **Mengkritisi** boleh; **menyetujui** tidak.

### 2.3 Predictive AI

**Tidak di MVP.** ([ADR-0006](adr/ADR-0006-no-predictive-mvp.md))

V2+ kalau dibangun, harus:
- Visualisasi riset, bukan signal.
- Probability band + caveat kuat.
- Naive baseline dibandingkan side-by-side.
- Label experimental jelas (lihat [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)).
- Tidak menghasilkan target price absolut.
- Tidak menghasilkan entry/exit instruction.
- Tidak boleh muncul di dashboard utama.

---

## 3. Output Schema (Wajib)

Setiap AI output user-facing **wajib** mengikuti structured schema. JSON Schema dipublish di `packages/core/ai/schemas/`. Runtime validator menolak output yang tidak conform; LLM call diulang sampai conform atau gagal hard.

### 3.1 `analysis_output` schema (untuk stock analysis & brief)

```typescript
{
  symbol: string,                    // canonical ticker
  analysis_date: string,             // ISO 8601
  prompt_template_id: string,        // e.g. "stock_brief.v3"
  model: string,                     // e.g. "claude-sonnet-4-6"
  evidence: Array<{
    type: "price" | "indicator" | "news" | "fundamental" | "journal",
    value: string,                   // human-readable
    source_ref: string,              // back to ai_log / row id
    freshness: string                // ISO 8601 of underlying data
  }>,                                // wajib non-empty
  bullish_view: string,
  bearish_view: string,
  uncertainty: string,               // wajib non-empty
  caveats: string[],                 // wajib length >= 1
  beginner_explanation: string,
  suggested_next_question: string,
  not_financial_advice: true         // wajib literal true
}
```

### 3.2 `journal_critique` schema (untuk pre-trade plan critic)

```typescript
{
  plan_id: string,
  checks: Array<{
    category: "thesis" | "invalidation" | "risk" | "catalyst" | "emotion" | "liquidity",
    status: "ok" | "weak" | "missing",
    finding: string,
    suggested_question: string
  }>,
  approval: never,                   // schema TIDAK PUNYA approval field
  overall_risk_flag: "green" | "amber" | "red" | "incomplete",
  caveats: string[]
}
```

Catatan: schema **tidak punya field `approval`**. Tidak mungkin secara struktural AI mengeluarkan "approved trade".

### 3.3 `news_summary` schema

```typescript
{
  news_id: number,
  url: string,
  summary: string,                   // max 3 kalimat
  affected_tickers: string[],        // canonical
  sentiment_label: "bullish" | "neutral" | "bearish" | "mixed",
  caveats: string[],                 // wajib non-empty kalau confidence < 0.7
  source_quality: "official" | "reputable_media" | "blog" | "unknown"
}
```

---

## 4. Hallucination Prevention (Teknis)

### 4.1 RAG-First
Setiap output AI **harus** berbasis retrieved data dari DB lokal (price, news, fundamental, journal). Tidak ada open-ended prompt tanpa konteks. Implementasi: `packages/core/ai/context_builder.py` membangun context payload dari DuckDB sebelum LLM call.

### 4.2 Structured Output Enforcement
- Gunakan `response_format` JSON Schema dari provider (Claude `tool_use` atau structured output API).
- Validator runtime (`packages/core/ai/validator.py`) reject output non-conform.
- Reject case: caveats kosong, evidence kosong, banned phrase ada, `not_financial_advice` ≠ `true`.

### 4.3 Multi-Step Verification
Pipeline default:
1. **Generate** — LLM produce structured output.
2. **Rule-based consistency check** — contoh: kalau RSI > 70 dan output bilang "oversold", flag inconsistency, reject.
3. **Confidence threshold** — output di bawah threshold (e.g. `< 0.6`) ditampilkan dengan warning visual + label "low confidence".
4. **Audit log** — semua step ter-log ke `ai_log` table (lihat [ARCHITECTURE.md §6](ARCHITECTURE.md)).

### 4.4 Banned Phrase Filter
Regex-based, run pada output sebelum render:

| Banned (auto-reject + retry) | Reason |
|---|---|
| `(saham|stock).*akan (naik|turun)` | Future certainty |
| `guaranteed|pasti untung|dijamin` | Profit promise |
| `(strong )?buy now|sell now|enter now` | Trade instruction |
| `this is safe|aman untuk dibeli` | Safety claim |
| `target price` (kecuali di scenario_analysis dengan caveat) | Implicit price target |

Kalau LLM berulang produce banned content (3× retry), gagalkan request dan log untuk review prompt template.

### 4.5 Bahasa Wajib & Dilarang

**Prefer:**
- *"Berdasarkan data yang tersedia..."*
- *"Indikator ini mungkin menyarankan..."*
- *"Ini risiko yang perlu di-check..."*
- *"Evidence-nya mixed karena..."*

**Banned (di-filter via §4.4):**
- *"Saham X akan naik."*
- *"Guaranteed."*
- *"Strong buy."*
- *"You should enter now."*
- *"This is safe."*

---

## 5. Prompt Template Governance

- Semua prompt di `prompts/system/*.md` — versioned, di-commit.
- Setiap prompt punya `template_id` (e.g. `stock_brief.v3`).
- Prompt **tidak boleh** berisi data privat / trade history personal (hardcoded).
- Perubahan prompt = PR + bump version (`stock_brief.v3` → `stock_brief.v4`).
- A/B testing prompt: out-of-scope MVP (overkill untuk single user).

---

## 6. Confidence Handling

Confidence di-set oleh LLM (kalau model support) atau by heuristic (jumlah evidence, freshness, caveat count). Mapping ke UI:

| Confidence | Display |
|---|---|
| ≥ 0.8 | Normal render |
| 0.6 – 0.8 | Subtle "moderate confidence" badge |
| < 0.6 | Warning banner: "Low confidence — verify manually" + caveat di-expand by default |
| Validation failed | Tidak render output, tampilkan error: "AI output tidak memenuhi standard. Coba lagi atau periksa data source." |

---

## 7. AI Privacy & Redaction

Sebelum kirim context ke LLM provider:
- Strip account number, broker ID, personal note yang ditandai `private:true`.
- Default: jangan kirim full journal ke LLM kecuali owner explicit opt-in per query.
- Portfolio: kirim hanya symbol + lots aggregate (sektor exposure), bukan avg price detail.
- Audit log boleh kontain input context (lokal only, tidak shared).

Lihat juga [SECURITY.md §AI-privacy](SECURITY.md).

---

## 8. Audit Trail

`ai_log` table (schema di [ARCHITECTURE.md §6](ARCHITECTURE.md)) menyimpan setiap call:
- `prompt_template_id`
- `model`
- `input_context` (after redaction)
- `output` (raw structured)
- `confidence`
- `caveats_count`
- `created_at`

UI menyediakan tombol **"Show reasoning trail"** di setiap AI panel → modal dengan data dari `ai_log`.

---

## 9. Operational Boundaries (No Automation)

Forbidden:
- Auto buy / sell (lihat [ADR-0004](adr/ADR-0004-no-broker-credential.md)).
- Auto-copy AI signal ke broker / paper trader.
- Auto-post AI analysis ke publik (Twitter, blog, dll).
- Auto-optimize strategy dari trade terbaru (overfit ke recency).
- Auto-increase position size setelah win.
- Auto-rationalize losing trade.

---

## 10. Failure Modes & Graceful Degradation

| Failure | Behavior |
|---|---|
| LLM provider down | UI tampilkan "AI tidak tersedia, evidence raw tetap bisa dibaca". Tidak fallback ke model "guessing" |
| Output validation gagal 3× | Hard fail, log untuk review. Tidak render best-effort output |
| Cost cap tercapai | Disable AI panel hari itu, raw data tetap tersedia |
| Token context overflow | Pesan jelas ke user: "Konteks terlalu besar. Kurangi range tanggal atau jumlah ticker." Tidak silently truncate |

---

## 11. Review Cycle

- Owner review banned-phrase log mingguan; tambah pattern baru kalau ada false-negative.
- AI usefulness metric (helpful/not, lihat [PRD_clean.md §9](PRD_clean.md)) dianalisis bulanan.
- Prompt template di-revise kalau metric anjlok.

---

## 12. Related Decisions

| ADR | Topik |
|---|---|
| [ADR-0004](adr/ADR-0004-no-broker-credential.md) | No broker credential storage (prevents auto-execute) |
| [ADR-0005](adr/ADR-0005-llm-wrapper.md) | LLM provider wrapper (swap-able) |
| [ADR-0006](adr/ADR-0006-no-predictive-mvp.md) | No predictive AI di MVP |
