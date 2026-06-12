# SahamLens Agentic Research Layer

Status: Proposal reference only. Not approved for implementation.

## 1. Ringkasan Eksekutif

**SahamLens Agentic Research Layer** adalah arah produk untuk menghubungkan SahamLens dengan Hermes, Telegram, dan Discord sebagai lapisan interaksi riset pribadi.

Tujuannya bukan membuat AI trading bot, sinyal beli/jual, atau sistem eksekusi otomatis. Tujuannya adalah mengurangi friksi saat owner sedang melakukan riset:

- bertanya cepat tentang ticker,
- memahami alasan alert,
- menangkap catatan journal,
- meninjau watchlist,
- membuat research snapshot,
- merapikan research queue,
- meninjau earnings/news context,
- mengubah informasi pasar yang tersebar menjadi decision support yang terstruktur.

Posisi produk yang disarankan:

> Research flows from dashboard to chat — without turning AI into a trading signal.

Ringkasan satu kalimat:

> Lapisan riset agentic privat yang memungkinkan owner melakukan query, triage, journal, dan review insight SahamLens melalui workflow Telegram/Discord berbasis Hermes, sambil menjaga local-first data, safety AI, dan keputusan manual.

## 2. Mengapa Ini Cocok untuk SahamLens

Arah ini cocok karena memperkuat identitas SahamLens yang sudah ada:

- **Local-first:** SahamLens tetap menjadi trusted local data core.
- **Single-user:** Workflow dirancang untuk owner pribadi, bukan SaaS atau komunitas publik.
- **Explainable:** Output tetap berbasis evidence, freshness, caveats, dan source reference.
- **Decision-support:** AI membantu memahami konteks, bukan memutuskan transaksi.
- **Public-repo-safe:** Integrasi harus menjaga private journal, portfolio, dan data lokal tidak bocor.
- **V1-aligned:** Memperluas watchlist, alerts, journal, screener, earnings, weekly review, strategy rules, dan AI brief tanpa mengubah scope menjadi trading engine.

Layer ini tidak menambah “lebih banyak indikator” sebagai fokus utama. Nilainya ada pada workflow continuity: dari market movement → pertanyaan riset → evidence → caveat → journal → rule review → keputusan manual.

## 3. Peran Hermes

Hermes sebaiknya berperan sebagai **orchestration layer**, bukan sumber kebenaran baru.

### Hermes Seharusnya Melakukan

- **Intent routing:** Memahami apakah user meminta ticker snapshot, alert explanation, journal draft, earnings summary, atau research queue action.
- **Tool calling:** Memanggil kemampuan SahamLens melalui kontrak eksplisit.
- **Policy gate:** Menolak permintaan buy/sell, target instruktif, auto-execution, dan public recommendation.
- **Chat adapter:** Menjembatani Telegram untuk quick workflow dan Discord untuk threaded research.
- **Response shaping:** Menyusun jawaban yang beginner-safe, caveated, dan evidence-based.

### Hermes Tidak Boleh Menjadi

- database kedua,
- calculation engine kedua,
- pembuat keputusan trading,
- broker connector,
- public publishing bot,
- signal seller,
- autonomous agent yang menulis data tanpa konfirmasi,
- sumber market fact yang bypass aturan freshness/data quality SahamLens.

Prinsip utama:

> Hermes orchestrates SahamLens. SahamLens remains the source of truth.

## 4. Use Case Telegram

Telegram paling cocok untuk workflow cepat, personal, dan low-friction.

### Morning Brief

Command contoh:

```text
/brief
```

Respons ideal:

- ringkasan konteks pasar,
- perubahan watchlist,
- alert penting,
- earnings/news item,
- stale data warning,
- suggested research questions,
- disclaimer singkat.

Tujuan: membantu owner memulai hari dengan konteks, bukan rekomendasi.

### Ticker Snapshot

Command contoh:

```text
/ticker BBCA
```

Respons ideal:

- identitas ticker,
- price/freshness context,
- indikator teknikal,
- fundamental snapshot,
- earnings/news context,
- evidence positif,
- evidence risiko,
- uncertainty,
- missing/stale data,
- suggested next question,
- disclaimer.

Tidak boleh menyimpulkan “beli”, “jual”, “masuk”, atau “aman”.

### Alert Triage

Contoh alert:

```text
Alert: BBCA volume above average
```

Respons/action ideal:

- jelaskan rule yang memicu alert,
- tampilkan data pemicu,
- tampilkan freshness/source,
- tampilkan kemungkinan false positive,
- tawarkan acknowledge,
- tawarkan mark false positive,
- tawarkan research brief,
- tawarkan journal draft.

Alert tetap menjadi context prompt, bukan instruksi transaksi.

### Journal Capture

Command contoh:

```text
/journal BBCA I almost entered because of breakout, but volume confirmation is weak. Emotion: FOMO.
```

Perilaku ideal:

- ubah raw note menjadi draft journal terstruktur,
- identifikasi field yang hilang,
- tanyakan klarifikasi,
- jangan persist tanpa konfirmasi eksplisit,
- jangan validasi trade sebagai benar/salah.

### Research Queue

Command contoh:

```text
/research add BBCA check whether thesis still holds after latest news
```

Perilaku ideal:

- menambahkan research task privat,
- menjaga intent awal,
- dapat diproses nanti menjadi structured research brief,
- tidak mengubah task menjadi sinyal.

## 5. Use Case Discord

Discord cocok untuk riwayat riset yang lebih panjang, threaded, dan terstruktur.

Channel privat yang disarankan:

```text
#morning-brief
#watchlist-alerts
#research-queue
#earnings-summary
#journal-review
#ticker-bbca
#ticker-bmri
```

Discord dapat mendukung:

- thread riset per ticker,
- weekly reflection digest,
- alert explanation thread,
- earnings analysis thread,
- research queue output,
- prompt refleksi journal,
- perbandingan ticker berbasis data SahamLens.

Discord tidak boleh menjadi:

- public recommendation community,
- social trading server,
- copy trading group,
- tempat advice untuk audience/client,
- channel publik sinyal saham.

Default yang disarankan: **private-only** sampai owner menyetujui boundary lain.

## 6. Konsep Fitur Inti

### Research Snapshot

Structured summary untuk satu ticker.

Isi minimum:

- ticker,
- data freshness,
- price context,
- indicator context,
- fundamental context,
- news/earnings context,
- journal context jika diizinkan,
- bullish/supporting evidence,
- bearish/risk evidence,
- uncertainty,
- caveats,
- suggested next question,
- disclaimer.

Bahasa harus tetap evidence-based. “Bullish evidence” boleh sebagai kategori observasi, bukan sinyal beli.

### Alert Explanation

Saat alert aktif, agent menjelaskan:

- rule apa yang aktif,
- data apa yang memicu,
- seberapa fresh data tersebut,
- potensi false positive,
- conflicting context,
- data yang belum tersedia,
- apa yang perlu diverifikasi manual.

Tidak boleh memakai istilah:

- “buy”,
- “sell”,
- “enter”,
- “exit”,
- “strong buy”,
- “aman dibeli”.

### Research Queue

Queue ringan untuk task riset milik owner.

Tujuan:

- mencegah riset tercecer,
- menjaga intent,
- mengubah ide spontan menjadi review terstruktur,
- mendukung follow-up dari Web UI atau Discord thread.

Contoh:

```text
BBCA — check whether the trend still supports the previous thesis after latest earnings/news.
```

### Journal Draft Assistant

Agent membantu mengubah catatan mentah menjadi draft journal.

Aturan:

- default draft-only,
- perlu konfirmasi sebelum write,
- tampilkan missing fields,
- boleh bertanya klarifikasi,
- tidak boleh menyetujui trade,
- tidak boleh memberi instruksi transaksi.

### Weekly Reflection Digest

Ringkasan mingguan untuk pembelajaran dan disiplin.

Isi:

- trade yang diambil,
- trade yang dilewati,
- rule violations,
- emotional pattern,
- checklist field yang sering kosong,
- learning topics minggu berikutnya.

Fokus: refleksi perilaku, bukan performance bragging.

### Earnings / News Research Companion

Ringkasan event menjadi:

- apa yang terjadi,
- ticker terdampak,
- sumber/evidence,
- confidence/caveats,
- hal yang perlu diverifikasi manual,
- kaitan dengan watchlist/journal jika diizinkan.

Harus menghindari klaim kausalitas berlebihan.

## 7. Safety dan Privacy Boundaries

### Hard No

Sistem tidak boleh:

- memberi rekomendasi beli/jual,
- mengatakan “strong buy”,
- mengatakan “enter now”,
- mengatakan “sell now”,
- menjanjikan profit,
- memberi target price sebagai instruksi,
- login ke broker,
- memasang order,
- melakukan auto-execution,
- mendukung copy trading,
- memberi public advice,
- memberi advice untuk audience/client,
- menyimpan data portfolio/journal nyata di luar private local storage,
- mengirim journal/portfolio detail ke LLM tanpa opt-in eksplisit.

### Required

Setiap output agentic harus menjaga:

- evidence,
- caveats,
- freshness,
- uncertainty,
- source references,
- disclaimer,
- audit trail,
- privacy redaction,
- manual confirmation untuk write actions.

### Privacy Default

Default privacy sebaiknya konservatif:

- journal context tidak otomatis dipakai,
- portfolio detail tidak otomatis disertakan,
- chat write action tidak langsung persist,
- Telegram/Discord hanya menampilkan data yang aman sesuai scope owner,
- LLM context harus minimum necessary.

## 8. AI Response Contract

Setiap respons agentic yang berkaitan dengan riset saham sebaiknya memenuhi kontrak ini:

- menyebut data yang digunakan,
- menyebut freshness/status data,
- menyebut evidence yang mendukung,
- menyebut evidence risiko atau konflik,
- menyebut caveat dan missing data,
- menyatakan bahwa ini bukan nasihat keuangan,
- memberi suggested next question,
- tidak memberi keputusan transaksi.

Contoh bahasa yang disarankan:

- “Berdasarkan data yang tersedia…”
- “Evidence saat ini mixed karena…”
- “Data ini perlu diverifikasi karena…”
- “Risiko yang perlu di-check…”
- “Pertanyaan berikutnya yang layak ditanyakan…”

Bahasa yang harus dihindari:

- “Saham ini akan naik.”
- “Strong buy.”
- “Masuk sekarang.”
- “Aman dibeli.”
- “Pasti profit.”
- “Target price pasti.”
- “Rekomendasi saya beli/jual.”

## 9. Contoh User Journey

### Morning

Owner menerima Telegram brief berisi:

- perubahan watchlist,
- freshness status,
- alert penting,
- earnings/news context,
- pertanyaan riset yang layak dicek.

Owner memilih satu ticker untuk ditinjau lebih lanjut.

### Market Hours

Alert masuk:

```text
BBCA volume above average
```

Telegram menjelaskan:

- rule yang aktif,
- data pemicu,
- freshness,
- potensi false positive,
- conflicting context,
- opsi acknowledge,
- opsi false-positive,
- opsi open research,
- opsi draft journal.

### Research Session

Owner bertanya di Discord:

```text
compare BBCA vs BBRI this week based on SahamLens data
```

Hermes mengambil konteks SahamLens dan menjawab:

- perbandingan data tersedia,
- freshness,
- evidence per ticker,
- risiko/missing data,
- caveat,
- pertanyaan lanjutan.

Tidak ada rekomendasi ticker mana yang harus dibeli.

### Before Trade

Owner menulis catatan cepat dari Telegram:

```text
/journal BBCA considering entry because breakout, but risk not fully defined. Emotion: FOMO.
```

Agent mengubah menjadi draft:

- thesis,
- emotion,
- missing invalidation,
- missing risk limit,
- pertanyaan klarifikasi,
- tombol/aksi konfirmasi sebelum simpan.

### End of Week

Discord menerima weekly digest:

- pola emosi,
- rule violations,
- checklist yang sering kosong,
- trade skipped/taken,
- learning topics.

Fokusnya refleksi dan disiplin, bukan hasil profit.

## 10. Open Product Questions untuk Owner Review

1. Apakah Telegram harus menjadi chat surface pertama dan Discord kedua?
2. Apakah Discord private-only selamanya, atau private by default saja?
3. Action apa saja yang boleh menulis ke local DB setelah konfirmasi?
4. Apakah journal context opt-in per command atau per session?
5. Apakah portfolio detail boleh pernah disertakan, atau hanya aggregate exposure?
6. Apakah alert actions perlu mendukung acknowledge/false-positive dari chat?
7. Apakah hasil research queue perlu disimpan sebagai local artifacts?
8. Apakah Hermes diperlakukan sebagai external agent terpisah atau local sub-process wrapper?
9. Apakah semua agent interaction masuk ke `ai_log` atau perlu `agent_log` terpisah?
10. Apa minimum useful daily Telegram brief?

## 11. Rekomendasi Keputusan

Rekomendasi: **lanjutkan, tetapi hanya sebagai ADR-first product direction.**

Decision statement yang disarankan:

> Accept the SahamLens Agentic Research Layer as a product direction, with Hermes as an orchestration layer over existing SahamLens data and workflows. The integration must remain private, local-first, evidence-based, caveated, non-advisory, and manually controlled. Telegram should be explored first for fast personal workflows, followed by Discord for threaded private research after Telegram value is proven.

Jangan langsung implementasi. Langkah berikutnya setelah owner setuju:

- tulis ADR boundary terlebih dahulu,
- kunci scope dan hard no,
- definisikan kontrak output agentic,
- baru turunkan ke execution plan terpisah.
