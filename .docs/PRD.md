# PRD — SahamLens

**Source of truth for:** Product scope, target user, vision, problem context, goals/non-goals, feature prioritization, product-level policy (automation, predictive AI, legal/ethical boundaries), success metrics, kill criteria.
**Tidak di sini:** Tech stack (→ [ARCHITECTURE.md](ARCHITECTURE.md)), AI rules teknis (→ [AI_BOUNDARIES.md](AI_BOUNDARIES.md)), security (→ [SECURITY.md](SECURITY.md)), disclaimer panjang (→ [TRADING_DISCLAIMER.md](TRADING_DISCLAIMER.md)), roadmap detail (→ [EXECUTION_BLUEPRINT.md](EXECUTION_BLUEPRINT.md)), UX detail (→ [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)), engineering rules (→ [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md)).

**Versi:** 1.1 (augmented dari v3-final — pull konteks rationale + product policy yang sebelumnya hilang)
**Tanggal:** 2026-05-18
**Status:** Approved — MVP-ready
**Owner:** Private single user
**Market scope:** Indonesia Stock Exchange (IDX)
**Supersedes:** PRD-SahamLens-v3-final.md (archived) — semua bagian tech/AI/security/schema/roadmap sudah pindah ke dokumen modular; PRD ini hanya menahan product scope + rationale.

---

## 1. Executive Summary

SahamLens = **personal trading companion** untuk satu trader retail Indonesia (pemula → intermediate) yang sedang belajar pasar saham IDX.

**Apa sistem ini:**
- Private dashboard untuk watchlist, indikator teknikal, fundamental snapshot, ringkasan berita, jurnal trading, risk checklist.
- Learning assistant berbasis AI yang menjelaskan indikator dalam konteks aktual.
- AI co-pilot yang **meringkas, membandingkan, dan menanyakan** — bukan memberi instruksi beli/jual final.
- Tool local-first yang repo-nya boleh publik (sharing teknologi), tanpa pernah meng-commit data portofolio pribadi.

**Apa sistem ini bukan:**
- Public SaaS fintech, broker, signal seller, autonomous trading bot, licensed investment advisor, prediction engine.

**Positioning satu kalimat:**

> SahamLens adalah jurnal + dashboard + AI tutor pribadi untuk membantu owner-nya berpikir lebih jernih sebelum dan sesudah trade — bukan untuk menggantikan keputusan owner.

---

## 2. Council Verdict & v1 Audit

### 2.1 Project ini seharusnya menjadi apa

Private **trading cockpit & learning workbench** yang membantu owner menjawab:

- Apa yang terjadi di watchlist saya hari ini?
- Saham mana yang perlu review lebih dalam?
- Apa kata indikator, dan apa keterbatasannya?
- Apa konteks market saat ini?
- Apa risiko yang saya lewatkan sebelum entry?
- Apakah trade sebelumnya konsisten dengan plan?
- Apakah saya membaik sebagai trader?

Prioritas desain: **clarity, repeatable workflow, explainability, data freshness, decision discipline**.

### 2.2 Project ini seharusnya tidak menjadi apa

Trade execution system · Public recommendation platform · Social / copy trading app · Multi-tenant fintech SaaS · Sistem yang menyimpan data finansial orang lain · Server-side scraper yang login ke akun broker · Model yang mengklaim prediksi harga · Enterprise architecture sebelum personal workflow terbukti berguna.

### 2.3 Audit terhadap arah PRD v1 yang ditolak

| Arah lama (PRD v1) | Masalah | Keputusan baru |
|---|---|---|
| Multi-user persona + subscription tier | Tidak align dengan personal use | Hapus |
| Pro/Premium/Enterprise + Free→Paid funnel | Tekanan produk palsu | Hapus |
| Multi-tenant DB + user management | Tidak perlu untuk satu user | Single local identity |
| TimescaleDB + Redis + Vector DB + BullMQ dari hari 1 | Beban operasional berlebihan | SQLite/DuckDB + cron lokal |
| Real-time tick data sebagai promise inti | Mahal, sulit, tidak esensial untuk belajar | EOD dulu, delayed intraday nanti |
| Twitter / Telegram / Stockbit stream sentiment | Noisy + ToS risk + over-trust risk | Experimental, non-MVP |
| AI signal BUY/HOLD/SELL | Bahaya psikologis untuk pemula | Evidence + risk prompt |
| Prophet / LSTM forecasting | Overfit + false confidence | Experimental only |
| Native mobile app | Distraksi sebelum workflow proven | PWA nanti |
| Community insights | Bertentangan dengan private-use | Hapus |
| Kubernetes / self-host scaling | Operational theater | Hapus |
| KPI: DAU/MAU, CAC, LTV, churn | Startup thinking | Learning & discipline metrics |
| Monetization tier | Out of scope total | Hapus |

**Root cause kesalahan PRD v1:** mencampur tiga goal yang inkompatibel — (1) personal trading support, (2) public fintech SaaS, (3) AI prediction product. PRD v3 memilih hanya goal (1).

**Verdict singkat:**

> Bangun sistem private decision-support yang kecil dan tajam dulu. Kalau belum bisa memperbaiki disiplin trading harian owner, skalanya tidak relevan.

---

## 3. Vision & Principles

### 3.1 Vision

SahamLens membantu owner-nya menjadi trader IDX yang lebih disiplin, terinformasi, dan reflektif, dengan mengubah data pasar yang berserakan menjadi insight yang dapat dijelaskan, checklist terstruktur, dan jurnal belajar.

### 3.2 Product Principles

1. **Personal first** — satu user, satu workflow, satu portofolio, satu learning journey.
2. **AI explains, user decides** — AI summarize, classify, compare, question. Tidak memutuskan.
3. **Evidence over confidence** — setiap insight wajib menampilkan source + freshness + caveat.
4. **Low maintenance** — tool lokal sederhana > infrastruktur cloud yang selalu hidup.
5. **Beginner-safe UX** — hindari pola "BUY now" hijau-merah manipulatif.
6. **No hidden automation** — no trade execution, no broker credential, no stealth scraping.
7. **Learning compounds** — journal & review loop sama pentingnya dengan chart.
8. **Honest uncertainty** — "tidak tahu / data kurang" > sinyal palsu.

---

## 4. Target User

### Primary user (satu-satunya)

Owner project. Profil:
- Beginner / early-intermediate trader IDX.
- Sedang belajar fundamental analysis, technical analysis, market psychology, risk management.
- Sedang mendalami tool seperti Stockbit.
- Mempelajari indikator: MA 5/10/15/50/200, volume, RSI 14, MACD, VWAP, support/resistance, MA crossovers.
- Memerlukan asisten yang **mengurangi kebingungan tanpa menciptakan false certainty**.

### Non-users (eksplisit)

Trader retail lain, paying customers, fund managers, signal subscribers, komunitas, klien broker, siapa pun selain owner.

Repo publik untuk sharing teknologi; sistem hanya melayani owner.

---

## 5. Problem Statement

### 5.1 Konteks IDX

- ±900 emiten, likuiditas tidak merata (top 50 vs second/third liner).
- Sentiment-driven, sensitif berita lokal & makro.
- Didominasi retail (>60% volume harian).
- Data publik tersebar: IDX, Stockbit, RTI, KSEI, media keuangan.

### 5.2 Pain points pemula

Terlalu banyak input fragmented sekaligus: price action, volume, MA, momentum indicators, fundamental ratios, news, noise stream, chart broker app, emosi pribadi, aturan risk yang tidak jelas. Hasil: analysis paralysis, FOMO, plan inkonsisten, post-trade learning lemah.

### 5.3 Job To Be Done

Mengubah daily market review menjadi **guided workflow** yang dapat diulang:

1. Check market context.
2. Review pergerakan watchlist.
3. Inspect indikator relevan.
4. Baca ringkasan news & event.
5. Bandingkan setup dengan personal strategy rules.
6. Selesaikan risk checklist.
7. Catat keputusan di journal.
8. Review outcome di kemudian hari.

---

## 6. Goals & Non-Goals

### 6.1 Goals (success indicator personal)

| Goal | Success indicator |
|---|---|
| Kurangi kebingungan pemula | Owner bisa jelaskan kenapa sebuah saham ada di watchlist |
| Percepat riset harian | Daily review selesai dalam 15–30 menit |
| Tingkatkan disiplin trading | Setiap trade punya thesis, invalidation, risk, post-review |
| Tingkatkan indicator literacy | Owner paham makna MA/RSI/MACD/VWAP/volume dalam konteks |
| Buat learning record durable | Journal entries terakumulasi jadi pelajaran reviewable |
| Cost rendah | MVP < Rp 200rb/bulan untuk LLM/API |
| Repo publik tetap aman | Tidak ada secret/credential/data portofolio ter-commit |

### 6.2 Non-goals (final, tidak dibahas lagi)

- Real-money auto-trading / order execution
- Public user onboarding
- Paid subscription / monetization
- Investment advice ke orang lain
- Guaranteed prediction
- Portfolio management untuk orang lain
- Scraping dengan stored brokerage credentials
- Social feed / recommendation system
- Enterprise observability stack di MVP

---

## 7. Feature Prioritization

### 7.1 MUST HAVE (MVP)

| # | Feature | Tujuan | Kebutuhan MVP |
|---|---|---|---|
| 1 | Watchlist | Fokuskan analisis | CRUD ticker, tag, annotate |
| 2 | Daily market brief | Konteks pagi | Summary IHSG + sektor + watchlist movers + news utama |
| 3 | Stock detail page | Inspect satu ticker | Chart, OHLCV, indikator, news, notes, AI explanation |
| 4 | Technical indicators | Structured chart reading | MA 5/10/15/50/200, volume avg, RSI 14, MACD |
| 5 | Indicator explainer | Belajar sambil analisis | Makna, current reading, common false signal |
| 6 | Fundamental snapshot | Hindari keputusan chart-only | Market cap, PER, PBV, ROE, DER, EPS, dividend yield |
| 7 | News summarizer (AI) | Reduce information overload | Summary + source + tanggal + ticker + caveat |
| 8 | Trade journal | Learning loop | Thesis, setup, entry/exit plan, emotion, result, lesson |
| 9 | Risk checklist | Cegah impulsive trade | Position size, max loss, stop, invalidation, catalyst, liquidity |
| 10 | Portfolio notes | Track exposure manual | Manual / CSV import — **no broker login** |
| 11 | AI chat assistant | Tanya kontekstual | Konteks: watchlist/news/journal lokal, wajib cite |
| 12 | Data freshness badge | Cegah keputusan dari data basi | Last update + source reliability per data group |

### 7.2 NICE TO HAVE (V1)

| Feature | Manfaat | Kapan |
|---|---|---|
| Custom screener | Cari kandidat dari rule sederhana | V1 |
| Alert rules | Notifikasi kondisi watchlist | V1 |
| Telegram notification | Alert personal sederhana | V1 |
| Earnings report summarizer | Belajar fundamental event lebih cepat | V1 |
| Backtesting-lite | Test rule indikator sederhana historis | V1/V2 |
| Performance analytics | Review kualitas journal & outcome | V2 |
| Strategy playbook | Encode setup pribadi | V2 |
| Local semantic search | Search note & news lama | V2 |
| Paper trading simulator | Latihan tanpa uang | V2 |
| PWA / mobile layout | Review dashboard di HP | V2 |

### 7.3 EXPERIMENTAL (terisolasi, post-MVP)

| Feature | Risiko | Aturan main |
|---|---|---|
| Predictive forecasting | Overfit + false confidence | Visualisasi riset only, **bukan signal** |
| Social sentiment | Noisy + manipulable | Context only, bukan evidence utama |
| Stockbit community analysis | ToS + bias | Manual notes/link |
| Chart pattern recognition | Sering unreliable | Learning aid only |
| RL strategy agent | Misleading untuk pemula | Jangan dibangun sebelum journal + backtest kuat |
| LLM-generated strategy suggestion | Overfit ke trade terbaru | Persetujuan manusia + caveat eksplisit |

**Global rule:** experimental **harus dipisahkan visual** dari decision-support core. Tidak boleh muncul di dashboard utama tanpa flag.

### 7.4 EXCLUDED (final)

| Feature | Alasan exclude |
|---|---|
| User account & subscription | Single-user private tool |
| Multi-tenant auth + RLS | Tidak ada user lain |
| Billing / payment | Tidak ada customer |
| Public API | Beban security & maintenance |
| Enterprise admin dashboard | Tidak ada organisasi |
| Native mobile app | PWA cukup |
| Social trading | Melanggar goal private |
| Copy trading | Risiko legal & etis tinggi |
| Broker credential storage | Risiko security & legal tinggi |
| Auto order execution | Out of scope total |
| Kubernetes | Operational theater |
| Real-time tick infra | Tidak justified di awal |
| Vector DB default | DuckDB full-text search cukup dulu |

---

## 8. Personal Workflow

### 8.1 Morning Review (sebelum pasar buka)

1. Buka dashboard, baca market brief.
2. Cek watchlist movers, buka 1–3 ticker yang perlu perhatian.
3. Review panel indikator:
   - **Trend:** MA alignment + slope.
   - **Momentum:** RSI + MACD.
   - **Participation:** volume vs average.
   - **Context:** support/resistance + news terbaru.
4. Tanya AI: *"Jelaskan apa yang berubah di ticker ini sejak note terakhir saya."*
5. Tandai status ticker: **Ignore / Watch / Prepare plan / Review existing position**.

### 8.2 Pre-Trade Checklist (wajib)

Sebelum trade, sistem **wajib** meminta plan tertulis: ticker, setup type, time horizon, entry reason, invalidation level, stop loss, target/exit, position size, max loss (Rupiah), news/catalyst, emotional state, *"What would prove this idea wrong?"*

AI **boleh mengkritisi** plan, **tidak boleh menyetujui** trade. Lihat [AI_BOUNDARIES.md](AI_BOUNDARIES.md).

### 8.3 During Market Hours

Sistem **memonitor** (tanpa eksekusi): price movement, volume spike, MA cross/retest, RSI extreme, MACD cross, news event, exposure. Notifikasi hanya untuk **user-defined rules**. False-positive ratio dilacak.

### 8.4 End-of-Day Review

Review trade dieksekusi → tambah journal note → bandingkan behavior vs plan → catat emosi & mistake pattern → generate daily lesson singkat (*what worked / what was unclear / what to review tomorrow*).

### 8.5 Weekly Review

Trade taken/skipped · Rule violations · Best/worst decisions · Emotional patterns · Repeated tickers · Learning topics minggu depan.

### 8.6 Daily Schedule (otomatis tapi soft)

```
07:00 WIB   Fetch pre-market data (cron lokal)
07:30 WIB   Generate Morning Brief
07:45 WIB   (optional) push ke Telegram
09:00 WIB   Market open — passive monitoring
            ├─ Anomaly detector (rule-based, every 5–10 min)
            └─ News fetcher (every 10 min)
12:00 WIB   Optional lunch check-in
15:00 WIB   Pre-close summary
16:00 WIB   Market close, EOD aggregation
16:30 WIB   Daily Wrap-Up + besok prep
22:00 WIB   Earnings / corporate action check
23:00 WIB   Archival lokal (no cloud sync untuk private data)
```

---

## 9. Indicator Strategy

### 9.1 Indicators MVP

| Indikator | Periode | Kategori | Tujuan pembelajaran |
|---|---|---|---|
| MA 5 | 5 | Trend (very short) | Sensitivitas jangka pendek |
| MA 10 | 10 | Trend (short) | Short-term momentum |
| MA 15 | 15 | Trend (short-mid) | Sering dipakai trader IDX |
| MA 50 | 50 | Trend (medium) | Trend menengah |
| MA 200 | 200 | Trend (long) | Trend struktural |
| Volume average | 20 | Participation | Konfirmasi |
| RSI | 14 | Momentum | Overbought / oversold |
| MACD | 12/26/9 | Momentum + trend | Cross & divergence |
| VWAP | intraday | Mean reversion | Reference price intraday (V1) |

### 9.2 Display Rule (5-Block Pattern)

Setiap indikator wajib tampil dengan 5 blok:
1. **What it measures**
2. **Current value**
3. **Simple interpretation** (kalimat awam)
4. **Common false signal**
5. **How it relates to user's time horizon**

Contoh:

```text
RSI 14 = 72
Mengukur: kecepatan & magnitudo perubahan harga (momentum).
Sering diartikan: momentum kuat, tetapi bisa berarti harga extended.
False signal umum: di trend kuat, RSI bisa stay >70 lama tanpa reversal.
Jangan dibaca sendirian. Cek trend, volume, support/resistance, dan news context.
```

Detail UI implementation: [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).

### 9.3 Anti-Patterns

- ❌ Badge "BUY" hijau berdasarkan satu indikator.
- ❌ "Sinyal: STRONG BUY".
- ❌ Skor numerik 1–10 tanpa breakdown.
- ✅ Statement berbasis evidence + counter-evidence.

---

## 10. Risk Management Rules (Product-Level)

| Rule | Default |
|---|---|
| Risk per trade | 0.5%–1% dari portfolio (beginner) |
| Averaging down | Hanya kalau eksplisit di-plan |
| Trade tanpa invalidation | Dilarang |
| Trade setelah emotional flag | Cooling-off wajib (lihat §13.4) |
| AI output sebagai sole reason | Dilarang |

Formula position sizing & tool detail: [`ARCHITECTURE.md §risk-engine`](ARCHITECTURE.md). Test requirements: [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md).

---

## 11. Predictive AI Reality Check

Predictive AI bisa edukatif, tapi **bukan trading edge yang reliable** untuk pemula by default.

**Kenapa berisiko:**
- IDX noisy, illiquid (di luar top 50), event-driven.
- Pola historis sering pecah.
- Pemula cenderung over-trust chart yang kelihatan scientific.
- Output Prophet / LSTM gampang overfit tanpa edge nyata.
- News, likuiditas, perilaku bandar, kebijakan makro, dan earnings sering mendominasi pola teknikal.

**Realistic use (kalau dibangun):**
- Belajar bagaimana asumsi model berperilaku.
- Menampilkan probability band dengan caveat kuat.
- Membandingkan naive baseline vs model output.
- Memahami ketidakpastian.
- Backtest hipotesis sederhana.

**Tidak diperbolehkan:**
- Target price absolut sebagai rekomendasi.
- Entry/exit instruction otomatis.
- Klaim win-rate tanpa metodologi backtest jujur.
- Advice untuk user lain.

**Rule operasional:** **JANGAN bangun predictive AI di MVP.** Bangun journal discipline + indicator literacy + risk management dulu. Forecasting masuk Experimental V2+.

---

## 12. Automation Boundaries

### 12.1 Boleh diotomatisasi

| Otomatisasi | Scope |
|---|---|
| Data refresh | Public / delayed OHLCV + news |
| Indicator calculation | Formula transparan |
| Daily brief generation | Summary dari data existing |
| Alert triggering | Rule yang user-defined |
| Journal summarization | Hanya note milik user sendiri |
| CSV import | User-exported portfolio file |
| Report generation | Daily / weekly personal review |

### 12.2 Tidak boleh diotomatisasi

| Otomatisasi | Alasan |
|---|---|
| Auto buy / sell | Risiko finansial & psikologis |
| Auto-copy signal dari AI | Berubah jadi signal system tidak berlisensi |
| Auto-scrape broker dengan stored credential | Security + ToS |
| Auto-post analysis publik | Bisa jadi investment advice ke orang lain |
| Auto-optimize strategy dari trade terbaru | Overfitting tinggi |
| Auto-increase position size setelah win | Mendorong perilaku berbahaya |
| Auto-rationalize losing trade | Mengganggu honest journaling |

---

## 13. Legal, Ethical, Psychological Boundaries

### 13.1 Legal positioning (Indonesia)

- OJK mengatur Wakil Manajer Investasi (WMI) dan WPEE.
- **Personal analytical tool untuk diri sendiri** = tidak butuh izin.
- **Memberi rekomendasi ke orang lain** = butuh izin WMI.
- **Mengelola dana orang lain** = butuh izin Manajer Investasi.

**Implikasi:** Sistem ini personal-use → aman tanpa izin. Kalau di masa depan **pernah** terpikir komersialisasi, konsultasi legal counsel dulu.

### 13.2 Disclaimer wajib

Disclaimer panjang & template: [TRADING_DISCLAIMER.md](TRADING_DISCLAIMER.md). Disclaimer muncul di:
- Footer dashboard.
- Setiap AI output (versi singkat).
- Setiap export report.
- README repo publik.

### 13.3 Ethical boundary

- Tidak mendorong overtrading.
- Tidak gamifikasi P&L cara yang meningkatkan risk-taking.
- Tidak menyembunyikan ketidakpastian.
- Tidak melatih user untuk patuh ke AI.
- Tidak membuat klaim publik berdasarkan data privat / incomplete.

### 13.4 Psychological boundary

- Sistem **tidak** mengirim notifikasi "saham X naik X%!" yang mendorong FOMO.
- Daily brief **selalu** mencantumkan reminder bahwa rule violation lebih merusak dari missed opportunity.
- Setelah loss, ada **cooling-off prompt**: minimal isi journal sebelum boleh akses pre-trade checklist berikutnya.

### 13.5 Financial-risk boundary

Sistem bisa memperbaiki kualitas proses, tapi **tidak bisa menjamin hasil trading**. Analisis yang lebih baik tidak menghilangkan risiko pasar. Owner wajib menerima ini sebelum trade.

---

## 14. Success Metrics (personal, bukan startup)

| Metric | Target |
|---|---|
| Daily review completion | 4–5 hari pasar / minggu |
| Time to daily context | < 5 menit setelah buka dashboard |
| Trade plan completeness | ≥ 90% trade punya thesis + invalidation + risk |
| Rule violation count | Trending turun |
| Journal review consistency | Weekly review selesai |
| AI usefulness | Owner tandai output helpful/not |
| Data freshness awareness | Dashboard selalu tampilkan source timestamp |
| Cost | MVP < Rp 200rb / bulan untuk LLM/API |
| Indicator literacy | Owner bisa jelaskan tiap indikator tanpa lihat penjelasan |

**Tidak dipakai:** DAU/MAU, churn, CAC, conversion, revenue, public user growth.

---

## 15. Kill / Pivot Criteria

Project ini **boleh** dihentikan. Lebih baik berhenti jujur daripada sunk cost.

1. **Tidak digunakan ≥ 4 minggu** → stop development, review apa yang salah.
2. **Owner mulai mengandalkan AI sebagai sole decision maker** → matikan AI recommendation, kembali ke indicator-only mode.
3. **Maintenance > nilai** (> 5 jam/minggu untuk fix data source padahal jarang dipakai) → cut feature.
4. **Owner berhenti trading** → repo jadi arsip belajar.
5. **Bug menyebabkan rugi finansial nyata** → freeze, root-cause, perbaiki sebelum lanjut.
6. **Cost LLM > Rp 500rb/bulan** tanpa value sebanding → batasi konteks atau matikan fitur AI tertentu.

---

## 16. Priority Order (Final Recommendation)

MVP terkuat **bukan** yang paling banyak AI-nya. MVP terkuat membuat owner:

1. Berhenti sejenak,
2. Memeriksa evidence,
3. Memahami indikator,
4. Mengukur risk dengan benar,
5. Menulis thesis,
6. Mereview outcome dengan jujur.

**Build order konkret:**

1. Watchlist clarity.
2. Indicator literacy.
3. News / context summarization.
4. Risk checklist.
5. Trade journal.
6. Weekly learning review.
7. **Baru kemudian:** screener, alert, backtest, experimental AI.

> Kalau sistem ini berhasil mencegah satu impulsive trade, membuat owner paham satu setup lebih dalam, dan menghasilkan satu jujur weekly review — ia sudah berguna.

---

## 17. Product Risk Register

(Risk teknis di [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) / [SECURITY.md](SECURITY.md). Yang di sini = product-level.)

| Risk | Likelihood | Impact | Mitigasi |
|---|---|---|---|
| Source data berubah / break | High | Medium | Adapter layer + multi-source fallback |
| LLM cost overrun | Medium | Medium | Model routing (Haiku untuk bulk), monthly cap |
| Owner over-rely ke AI → loss | Medium | High | UX dorong critical thinking + cooling-off setelah loss |
| Scope creep balik ke "fitur SaaS" | Medium | Medium | PRD ini sebagai constitution; review tiap quarter |
| Owner berhenti trading | Medium | — | Bukan risk — valid kill criteria (§15) |
| ToS violation source data | Medium | Medium | Pakai source resmi, dokumentasikan |
| Burnout maintainer (= owner) | Medium | High | Kill criteria §15 explicit; tidak ada kewajiban ke user lain |

---

## 18. Acceptance Criteria

### Product
- Personal/private use eksplisit.
- MVP tanpa monetization, public user, broker credential.
- AI boundary eksplisit (→ [AI_BOUNDARIES.md](AI_BOUNDARIES.md)).
- Journal = core feature, bukan afterthought.
- Risk checklist wajib sebelum trade planning.
- Predictive AI tidak di-MVP.

### Technical
- MVP jalan lokal (→ [ARCHITECTURE.md](ARCHITECTURE.md)).
- Data privat tidak butuh cloud storage.
- Kegagalan data source visible ke owner.
- Indicator calc testable, coverage ≥ 90% (→ [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md)).
- AI output mengikuti structured schema (→ [AI_BOUNDARIES.md](AI_BOUNDARIES.md)).

### Safety
- Tidak ada bahasa command buy/sell.
- Tidak ada auto execution.
- Tidak ada hidden scraping.
- Tidak ada advice ke orang lain.
- Tidak ada private data di repo publik (→ [SECURITY.md](SECURITY.md)).

---

## 19. Glossary

- **IHSG** — Indeks Harga Saham Gabungan.
- **IDX** — Indonesia Stock Exchange (Bursa Efek Indonesia).
- **KSEI** — Kustodian Sentral Efek Indonesia.
- **OJK** — Otoritas Jasa Keuangan.
- **WMI / WPEE** — Wakil Manajer Investasi / Wakil Perantara Pedagang Efek.
- **RTI** — Real-Time Information.
- **RAG** — Retrieval-Augmented Generation.
- **EOD** — End-of-Day (data).
- **OHLCV** — Open / High / Low / Close / Volume.
- **PER / PBV / ROE / DER / EPS** — rasio fundamental dasar.
- **VWAP** — Volume-Weighted Average Price.
- **MA** — Moving Average.
- **RSI** — Relative Strength Index.
- **MACD** — Moving Average Convergence Divergence.

---

## 20. Change Log

| Versi | Tanggal | Catatan |
|---|---|---|
| 1.0 | 2026-05-16 | Refactor dari `PRD-SahamLens-v3-final.md`: tech, AI, security, schema, roadmap dipindah ke dokumen modular. Hanya product scope yang tersisa. |
| 1.1 | 2026-05-18 | Augment dari v3-final: tambah Council Verdict + v1 audit (§2), Vision & Principles (§3), IDX context di Problem Statement (§5.1), Predictive AI Reality Check (§11), Automation Boundaries (§12), Legal/Ethical/Psychological boundaries (§13), Priority Order (§16), Product Risk Register (§17), Glossary (§19). Rename file `PRD_clean.md` → `PRD.md`. |
