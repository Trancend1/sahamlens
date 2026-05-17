# TRADING_DISCLAIMER — SahamLens

**Source of truth for:** Legal positioning, disclaimer text canonical, financial-risk boundary, ethical & psychological boundary, mandatory display locations.
**Tidak di sini:** AI rules (→ [AI_BOUNDARIES.md](AI_BOUNDARIES.md)), data ToS (→ [DATA_SOURCES.md](DATA_SOURCES.md)), product scope (→ [PRD_clean.md](PRD_clean.md)).

**Versi:** 1.0
**Status:** Active — **legally binding text. Edit hanya via PR + ADR.**

---

## 1. Legal Positioning (Indonesia)

- OJK mengatur **Wakil Manajer Investasi (WMI)** dan **Wakil Perantara Pedagang Efek (WPEE)**.
- **Personal analytical tool untuk diri sendiri** → tidak butuh izin.
- **Memberi rekomendasi ke orang lain** → butuh izin WMI.
- **Mengelola dana orang lain** → butuh izin Manajer Investasi.

**Implikasi:** SahamLens adalah personal-use system → tidak butuh izin OJK. **Jika di masa depan terpikir komersialisasi atau memberi rekomendasi publik**, konsultasi legal counsel dulu.

Lihat juga [PRD_clean.md §1](PRD_clean.md) untuk positioning produk.

---

## 2. Canonical Disclaimer Text

Versi ini adalah master. Semua tempat lain (README, footer UI, AI output, export report) **wajib** reference text ini, bukan menulis ulang.

### 2.1 Full version (untuk README, `DISCLAIMER.md`, export report header)

```text
DISCLAIMER

SahamLens adalah personal learning & analysis tool, bukan investment advice.

- Bukan rekomendasi investasi resmi.
- Bukan trading execution platform.
- Bukan layanan manajemen investasi.
- Bukan layanan perantara efek.
- Keputusan trading sepenuhnya tanggung jawab pengguna.
- Past performance tidak menjamin hasil masa depan.
- Data sumber bisa delayed, incomplete, atau tidak akurat.
- Terms of service platform sumber data harus dihormati.
- Konsultasikan financial advisor berlisensi untuk keputusan material.

Penggunaan tool ini berarti pengguna menerima bahwa risiko finansial dari
keputusan trading adalah tanggung jawab pengguna sepenuhnya, dan tool ini
tidak memberi jaminan apa pun terkait akurasi, kelengkapan, atau hasil.
```

### 2.2 Short version (untuk UI footer, AI output footer)

```text
AI-generated • not financial advice • verify source & freshness
```

### 2.3 Mid version (untuk AI output panel header)

```text
Output AI ini adalah summary edukasi, bukan investment advice.
Verifikasi data source & freshness sebelum mengambil keputusan trading.
Lihat DISCLAIMER untuk detail.
```

---

## 3. Mandatory Display Locations

| Lokasi | Versi | Catatan |
|---|---|---|
| `DISCLAIMER.md` (root repo) | Full | Single file kanonik, link dari README |
| `README.md` | Full | Section "Disclaimer" |
| UI dashboard footer | Short | Always visible (sticky atau footer) |
| Stock detail page (AI panel header) | Mid | Sebelum AI output |
| AI output (auto-attached field `not_financial_advice: true`) | Schema-level | Lihat [AI_BOUNDARIES.md §3](AI_BOUNDARIES.md) |
| Export report (CSV / PDF) | Full | Header file |
| Notification (Telegram) | Short (1 baris) | Sufficient |

Tidak menambah disclaimer ke setiap chat message (visual noise). Owner sudah tahu konteks via panel header.

---

## 4. Financial-Risk Boundary

- Sistem **bisa** memperbaiki kualitas proses (disiplin, dokumentasi, evidence-checking).
- Sistem **tidak bisa** menjamin hasil trading.
- Analisis yang lebih baik **tidak menghilangkan** risiko pasar (volatilitas, likuiditas, event risk, behavioral risk).
- Owner wajib menerima ini sebelum trade.

UI tidak menampilkan estimasi "win rate" atau "expected return" sebagai angka tunggal — selalu dengan range + caveat metodologi.

---

## 5. Ethical Boundary

Tool ini tidak boleh:
- Mendorong overtrading.
- Gamifikasi P&L dengan cara yang meningkatkan risk-taking (streak counter, leaderboard, confetti).
- Menyembunyikan ketidakpastian.
- Melatih user untuk patuh ke AI (lihat [AI_BOUNDARIES.md](AI_BOUNDARIES.md)).
- Membuat klaim publik berdasarkan data privat / incomplete.

Operationalisasi di [DESIGN_SYSTEM.md §1, §3, §6](DESIGN_SYSTEM.md).

---

## 6. Psychological Boundary

- Sistem **tidak** mengirim notifikasi "saham X naik X%!" yang mendorong FOMO. Hanya notifikasi untuk user-defined rules.
- Daily brief **selalu** mencantumkan reminder: *"Rule violation lebih merusak dari missed opportunity."*
- Setelah loss trade ditandai di journal:
  - **Cooling-off prompt** wajib (minimal isi journal entry dengan field emotion + lesson).
  - Pre-trade checklist berikutnya di-gate sampai cooling-off selesai.
  - Default cooling-off: sampai journal entry submitted. Owner dapat extend ke timer (e.g. 1 hari) via config.

---

## 7. Edit Process

1. Buka PR.
2. Tulis ADR singkat di `adr/` (`ADR-NNNN-disclaimer-update.md`) — jelaskan kenapa text berubah, apa yang berubah, apakah konsultasi legal sudah dilakukan.
3. Update semua mandatory display location.
4. Bump versi dokumen di header.

Tidak ada edit silent. Disclaimer = governance.

---

## 8. References

- [PRD_clean.md](PRD_clean.md) — positioning produk.
- [AI_BOUNDARIES.md](AI_BOUNDARIES.md) — auto-attached disclaimer di output AI.
- [SECURITY.md §5](SECURITY.md) — public repo rules (apa boleh & tidak di-publish).
- OJK Regulations: https://www.ojk.go.id/
