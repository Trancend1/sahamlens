# CONTRIBUTING — SahamLens

**Source of truth for:** Cara berkontribusi tanpa mengubah arah personal-use, scope yang welcome vs declined, PR etiquette, contributor-facing onboarding.
**Tidak di sini:** Code style (→ [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md)), security rules (→ [SECURITY.md](SECURITY.md)), product scope (→ [PRD_clean.md](PRD_clean.md)).

**Versi:** 1.0
**Status:** Active

---

## 1. Project Identity (Baca Ini Dulu)

SahamLens adalah **personal trading companion untuk satu user (owner)**. Repo publik untuk sharing teknologi & kontribusi open source, **bukan** karena project ini sedang membangun produk untuk pengguna lain.

**Konsekuensi praktis:**
- Tidak ada SaaS roadmap.
- Tidak ada multi-user feature.
- Tidak ada monetization.
- Tidak ada SLA support.
- Owner berhak menolak kontribusi yang menggeser arah project — bukan karena mutu kode, tapi karena fit dengan personal-use philosophy.

Kalau Anda ingin SaaS fintech IDX, fork repo ini dan bangun project Anda sendiri. Itu sangat di-encourage.

---

## 2. Yang Welcome (Contributions yang Cocok)

| Kategori | Contoh |
|---|---|
| **Bug fix** | Test failure, data source breakage fix, edge case di indicator formula |
| **Test coverage** | Property-based tests, edge case coverage, golden fixtures |
| **Dokumentasi** | Klarifikasi, typo, translasi (Indonesian/English), contoh penggunaan |
| **Data adapter baru** | Source data publik tambahan yang fit dengan [DATA_SOURCES.md](DATA_SOURCES.md) |
| **Indicator baru (educational)** | Indikator yang menambah literacy + 5-block explanation lengkap |
| **Tooling DX** | Pre-commit improvement, CI speedup, lint config |
| **Accessibility/UX improvement** | Kontras, keyboard navigation, freshness clarity |
| **Performance** | Query optimization, bundle size cut, ingestion speedup |
| **ADR proposal** | Diskusi alternatif teknis dengan trade-off jelas |

---

## 3. Yang Declined (Hindari Effort Anda)

| Kategori | Alasan |
|---|---|
| Multi-user / auth | Out of scope ([PRD_clean.md §4.4](PRD_clean.md)) |
| Subscription / billing | Tidak ada monetization |
| Auto-trading / order execution | Forbidden ([ADR-0004](adr/ADR-0004-no-broker-credential.md)) |
| Broker credential storage / OAuth | Forbidden |
| AI yang generate "BUY/SELL recommendation" | Melanggar [AI_BOUNDARIES.md](AI_BOUNDARIES.md) |
| Predictive AI di MVP | [ADR-0006](adr/ADR-0006-no-predictive-mvp.md) — V2+ kalau pun ada |
| Social trading / copy trading / public feed | Out of scope |
| Native mobile app | PWA cukup, prioritas V2 |
| Kubernetes / scaling infra | Operational theater untuk single-user |
| "Just in case" abstraction | Anti-pattern ([ENGINEERING_STANDARDS.md §11](ENGINEERING_STANDARDS.md)) |

Kalau ragu apakah kontribusi Anda fit, **buka issue dulu** sebelum tulis kode.

---

## 4. Sebelum Mulai

1. Baca [PRD_clean.md](PRD_clean.md) — paham scope.
2. Baca [AI_BOUNDARIES.md](AI_BOUNDARIES.md) + [SECURITY.md](SECURITY.md) — paham governance.
3. Baca [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) — paham code style.
4. Cek issue tracker apakah kerjaan sudah ada owner.
5. Untuk fitur baru: buka issue dulu dengan label `proposal` — dapat feedback sebelum effort besar.

---

## 6. Setup Lokal (Lihat README Root)

Repo `README.md` punya setup steps. Inti:

```bash
# 1. Clone
git clone <repo>
cd sahamlens

# 2. Copy env template
cp .env.example .env.local
# edit .env.local kalau perlu API key

# 3. Install deps
pnpm install
uv sync           # atau: poetry install

# 4. Init DB (sample data)
python scripts/init_db.py --sample

# 5. Pre-commit
pre-commit install

# 6. Run
pnpm dev          # Next.js
```

**Wajib:** tidak pernah menulis ke `data/private/**` di branch Anda. Sample data only.

---

## 7. PR Workflow

1. **Fork** atau buat branch (kalau collaborator).
2. **Branch name:** `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, `chore/<topic>`.
3. **Commit:** Conventional Commits ([ENGINEERING_STANDARDS.md §6.2](ENGINEERING_STANDARDS.md)).
4. **Test:** semua test passing lokal. Untuk financial calc: coverage ≥ 90%.
5. **Lint:** pre-commit hooks pass.
6. **PR title:** ringkas, imperative, lowercase first word setelah prefix. Contoh: `feat(indicators): add bollinger bands with 5-block explainer`.
7. **PR body wajib:**
   - **Apa** yang berubah (1–3 kalimat).
   - **Why** — link ke issue / ADR / line di PRD.
   - **Boundary check** — konfirmasi tidak melanggar AI/security/scope.
   - **Test plan** — apa yang di-test, hasil.
   - Screenshot kalau menyentuh UI.
8. **Ukuran PR:** bias kuat ke kecil (< 400 LOC diff). PR besar di-encourage split.
9. **CI hijau** wajib sebelum merge.
10. **Review:** owner self-merge OK. Public contributor: tunggu owner approve.

---

## 8. ADR (Architecture Decision Record)

Kalau kontribusi Anda introduce keputusan teknis besar (library baru, boundary baru, kebijakan baru), tulis ADR di `.docs/adr/`:

- Format: lihat [.docs/README.md §Recommended ADR Strategy](README.md).
- Penomoran: ambil nomor berikutnya sequential.
- Status mulai: `proposed`. Owner akan ubah ke `accepted` saat merge.

Contoh saat ADR perlu:
- Ganti library chart.
- Tambah dependency dengan license non-permissive.
- Ubah storage strategy.
- Tambah / ubah AI provider routing.

Tidak perlu ADR untuk:
- Bug fix.
- Test coverage improvement.
- Doc edit.
- Refactor tanpa API change.

---

## 9. Code Review Etiquette

Untuk reviewer (biasanya owner):
- Fokus ke: correctness, boundary compliance, test adequacy, naming clarity.
- Hindari: bikeshed (warna button, comment style — sudah ada lint).
- Approve dengan 1 reviewer cukup (solo project).

Untuk contributor:
- Respond ke comment dalam 1–2 minggu, atau PR dianggap stale & closed.
- Tidak ada kewajiban panjang back-and-forth — kalau scope-nya divergen dari arah project, akan declined dengan penjelasan singkat.

---

## 10. Issue Etiquette

### Bug report wajib include:
- Versi commit hash.
- Steps to reproduce.
- Expected vs actual.
- Logs (sanitized — tidak ada secret / data privat).
- Lingkungan (OS, Python version, Node version).

### Feature proposal wajib include:
- Problem statement.
- Bagaimana fit dengan personal-use philosophy.
- Alternatif yang dipertimbangkan.
- Dampak ke security / AI boundary / data layer.

Issue yang tidak fit scope ditutup dengan label `out-of-scope` + penjelasan singkat — tidak personal, ini just project alignment.

---

## 11. Communication

- **Issue / PR comment:** primary channel.
- **Tidak ada Discord/Slack/Telegram** — single-user project, low-traffic.
- **Email owner:** lihat git commit author. Hanya untuk security report (lihat §12).

---

## 12. Security Report

**Jangan** buka public issue untuk security vulnerability. Email owner langsung (lihat git author). Owner respond best-effort — tidak ada SLA. Lihat [SECURITY.md §6](SECURITY.md) untuk incident response.

---

## 13. License & Attribution

- Repo MIT (atau permissive equivalent — lihat root `LICENSE`).
- Contribution di-deem dilisensikan dengan MIT juga (standard inbound=outbound).
- Tidak ada CLA (contributor license agreement) — bagi solo project, friction tidak sepadan.
- Credit di commit message Co-authored-by line.

---

## 14. Code of Conduct (Singkat)

- Hormati waktu reviewer & contributor lain.
- Tidak ada harassment, diskriminasi, spam.
- Diskusi teknis: separate code from person.
- Owner reserve right untuk close issue/PR/ban contributor yang melanggar.

---

## 15. Acknowledgements

Project ini adalah personal learning tool. Kontribusi Anda — baik bug fix, doc fix, atau diskusi proposal yang akhirnya declined — punya nilai. Terima kasih sudah baca sampai sini.
