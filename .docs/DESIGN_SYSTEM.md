# DESIGN_SYSTEM — SahamLens

**Source of truth for:** UI philosophy, design principles, color & visual rules, beginner-safe interaction patterns, layout structure, indicator display pattern.
**Tidak di sini:** Tech stack (→ [ARCHITECTURE.md](ARCHITECTURE.md)), AI output schema (→ [AI_BOUNDARIES.md](AI_BOUNDARIES.md)), accessibility test rules (→ [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md)).

**Versi:** 1.0
**Status:** Active

---

## 1. Design Philosophy

> Dashboard ini melayani satu trader yang sedang belajar. Tujuan UI: **mengurangi kebingungan tanpa membuat false certainty.**

### Tiga prioritas (urutan tegas)
1. **Clarity** — informasi yang penting harus muncul lebih cepat dari yang dekoratif.
2. **Honesty** — freshness, source, dan ketidakpastian wajib visible.
3. **Calmness** — hindari pola yang melatih dopamine spike (animasi besar saat profit/loss).

### Anti-philosophy (apa yang dihindari)
- Bloomberg terminal density tanpa konteks.
- Robinhood gamification (confetti, animasi pump).
- "Crystal ball" widgets ("AI says BUY!").
- Enterprise dashboard maximalism (60 KPI di satu layar).
- Dark patterns yang mendorong overtrading.

---

## 2. Layout Principles

### 2.1 Dashboard (home)
**Wajib tampil:**
1. Market condition summary (IHSG + sektor utama, 1-line per).
2. Watchlist table (ticker, price, % change, volume vs avg, status tag).
3. "Needs attention" list (sort by anomaly / change magnitude).
4. **Data freshness indicator per panel** (timestamp + source).
5. Latest journal reminder ("Belum review trade BBCA dari 3 hari lalu").
6. Learning topic of the day (rotating, 1 baris).

**Wajib tidak:**
- Flashy "BUY/SELL" badge.
- Overconfident prediction.
- Enterprise-style overloaded navigation.
- Social leaderboard / community feed.

### 2.2 Stock Detail Page (urutan vertikal)
1. Price chart (default candlestick + indicator overlay toggle).
2. Indicator overlay controls.
3. **Indicator explanation panel** (pola 5-blok, §4).
4. Fundamental snapshot card.
5. Related news (dengan freshness per item).
6. AI summary panel (dengan evidence + caveat, lihat [AI_BOUNDARIES.md §output-schema](AI_BOUNDARIES.md)).
7. Personal thesis & notes.
8. "Create Trade Plan" CTA (membuka pre-trade checklist).

### 2.3 Journal Page
- Form structured, bukan blank canvas.
- Required field: ticker · setup · why interested · entry plan · stop/invalidation · target/exit · risk amount · emotion.
- Optional: screenshot · link.
- Review date scheduler.
- List view: filter by status (planned/open/closed/skipped), sort by created/reviewed.

---

## 3. Color & Visual Rules

### 3.1 Color Semantic

| Color | Penggunaan | Penggunaan TERLARANG |
|---|---|---|
| Green (`green-600`) | Trend up indicator (kecil, kalem) | Tombol "BUY", celebration |
| Red (`red-600`) | Trend down indicator (kecil, kalem) | Tombol "SELL", panic |
| Amber/Yellow (`amber-500`) | "Extreme" indicator (RSI>70/<30, vol>3× avg), warning | Default state |
| Slate/Neutral | Default state, body text | — |
| Blue (`blue-600`) | Action CTA non-trading (buka plan, save note) | Trading action |

**Aturan:** indikator yang "extreme" → **neutral warning color** (amber), bukan merah/hijau langsung. Mencegah pembacaan instan sebagai signal.

### 3.2 Animation

- Tidak ada confetti, tidak ada flashing.
- Equity curve transition: 200ms ease-out max.
- Number change: count-up dimatikan default (membuat number "real-time" feel mengandung kebenaran palsu).
- Toast notification: 1.5s, non-intrusive corner.

### 3.3 Typography
- Body: system sans (Inter via Next.js font).
- Numbers (price, volume): tabular-nums (`font-variant-numeric: tabular-nums`).
- Heading: weight 600, **tidak** uppercase (uppercase bikin teriak).

### 3.4 Iconography
- Lucide icons (sudah ter-bundle dengan shadcn/ui).
- Tidak ada emoji di production UI (hanya boleh di journal note user-typed).

---

## 4. Indicator Display Pattern (5-Block Rule)

Wajib untuk setiap indikator di stock detail page.

```
┌───────────────────────────────────────────────────┐
│  RSI 14 = 72                                       │  ← (2) Current value
├───────────────────────────────────────────────────┤
│  Mengukur: kecepatan & magnitudo perubahan harga  │  ← (1) What it measures
│  (momentum).                                       │
├───────────────────────────────────────────────────┤
│  Sering diartikan: momentum kuat — tapi bisa juga │  ← (3) Simple interpretation
│  berarti harga sudah extended.                     │
├───────────────────────────────────────────────────┤
│  ⚠ False signal umum: di trend kuat, RSI bisa     │  ← (4) Common false signal
│  stay >70 lama tanpa reversal.                     │
├───────────────────────────────────────────────────┤
│  Untuk swing harian: jangan dibaca sendirian. Cek │  ← (5) Relate to user horizon
│  trend, volume, support/resistance, dan news       │
│  context.                                          │
└───────────────────────────────────────────────────┘
```

Komponen React: `<IndicatorCard indicator="rsi_14" value={72} horizon="swing" />` — konten 5-blok di-load dari `packages/core/indicators/explanations/<indicator>.md` (single source of truth untuk teks edukasi).

---

## 5. Component Direction (shadcn/ui)

Default ke shadcn/ui primitives. **Tidak menulis custom design system primitives kecuali tidak ada di shadcn.**

| Need | shadcn component |
|---|---|
| Form | `Form` + `react-hook-form` + `zod` |
| Table | `DataTable` (TanStack Table integration) |
| Modal | `Dialog` |
| Tooltip / freshness badge | `Tooltip` + `Badge` |
| Chart | bukan shadcn — pakai `lightweight-charts` atau `Recharts` (lihat [ARCHITECTURE.md](ARCHITECTURE.md)) |
| Toast | `Sonner` |
| Dropdown | `Select` / `Combobox` |

Custom component yang **perlu** dibuat (di `packages/ui/`):
- `IndicatorCard` (5-block pattern)
- `FreshnessBadge` (timestamp + source + status)
- `AIOutputPanel` (evidence + caveat layout — bind ke schema dari [AI_BOUNDARIES.md](AI_BOUNDARIES.md))
- `RiskChecklistForm`
- `JournalEntryForm`
- `TradePlanCritic` (renders LLM critique tanpa approve/reject button)

---

## 6. Interaction Patterns

### 6.1 Beginner-Safe Defaults
- Setiap angka P&L wajib diiringi context: time horizon, % portfolio, max drawdown sebelumnya.
- Setiap action yang mengubah state journal: confirmation step ("Tulis 1 kalimat alasan untuk melanjutkan").
- Setelah loss trade ditandai: cooling-off prompt sebelum akses pre-trade checklist berikutnya (lihat [PRD_clean.md §8](PRD_clean.md)).

### 6.2 Freshness UX
Setiap data panel wajib punya `<FreshnessBadge />`:
- Hijau (kecil): < 1 jam.
- Amber: 1–24 jam.
- Red: > 24 jam atau fetch gagal.
- Hover tooltip: timestamp ISO + source name.

Kalau freshness red, **CTA trade-plan harus disable** dengan pesan "Data terlalu basi untuk decision".

### 6.3 AI Output Display
- Selalu di panel terpisah, bukan diselipkan ke chart.
- Wajib header "AI-generated • cite source • not financial advice".
- Caveat ditampilkan **tidak collapsed by default**.
- Tombol "Show reasoning trail" → membuka modal dengan input context + prompt template ID dari `ai_log`.

### 6.4 No-Goals Pattern
- Tidak ada "Quick Buy" / "1-click trade".
- Tidak ada notification "saham X naik X%!" tanpa user-defined rule.
- Tidak ada leaderboard, achievement, atau streak counter.

---

## 7. Responsive

- Desktop-first (owner workflow di laptop).
- Tablet: support kolom layout adaptive.
- Mobile: read-only di MVP (PWA full di V2). Pre-trade checklist **tidak boleh** dilakukan di mobile (ada checklist invalidation).

---

## 8. Accessibility (Minimal)

- Kontras WCAG AA untuk semua text.
- Tombol & form: keyboard navigable.
- Color tidak jadi satu-satunya information channel (selalu ada label/icon).
- Screen reader: tidak prioritas MVP (single-user, owner tidak butuh). Tidak melarang, tapi tidak audit.

---

## 9. Design Decisions Log

Keputusan visual besar (mis. "ganti dari Recharts ke lightweight-charts") tulis sebagai ADR. Decisions kecil (pilihan warna spesifik, copy adjustment) cukup di commit message.
