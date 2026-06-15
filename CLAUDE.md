# CLAUDE.md — SahamLens

SahamLens adalah *personal trading companion* untuk satu *retail* trader IDX. *Local-first*, publik-*repo-safe*, dan AI-*assisted*. AI menjelaskan; *user* memutuskan. **Bukan** broker, *signal service*, *portfolio manager*, atau SaaS.

> **Phase aktif:**---*
> **Status *planning*:** *frozen*
> **Branch:** `---`

Dokumen ini adalah *sibling* dari [`AGENTS.md`](AGENTS.md). Isi dan struktur mengikuti *template* yang sama. Detail agen, *track*, dan mekanisme *orchestration* ada di AGENTS.md — file ini ringkas untuk akses cepat.

---

## 1. *Documentation Map*

| Topik | *Source of Truth* |
|---|---|
| *Scope* produk, *goal*, non-*goal* | [.docs/PRD.md](.docs/PRD.md) |
| Arsitektur sistem, batas modul | [.docs/ARCHITECTURE.md](.docs/ARCHITECTURE.md) |
| Eksekusi, *sprint backlog* | [.docs/EXECUTION_BLUEPRINT.md](.docs/EXECUTION_BLUEPRINT.md) |
| *Data providers, freshness, coverage* | [.docs/DATA_SOURCES.md](.docs/DATA_SOURCES.md) |
| Aturan AI, batasan output, keamanan | [.docs/AI_BOUNDARIES.md](.docs/AI_BOUNDARIES.md) |
| Privasi, *secrets, threat model* | [.docs/SECURITY.md](.docs/SECURITY.md) |
| *Disclaimer* *trading* | [.docs/TRADING_DISCLAIMER.md](.docs/TRADING_DISCLAIMER.md) |
| Aturan UI, *visual vocabulary* | [.docs/DESIGN_SYSTEM.md](.docs/DESIGN_SYSTEM.md) |
| *Workflow engineering* | [.docs/ENGINEERING_STANDARDS.md](.docs/ENGINEERING_STANDARDS.md) |
| Keputusan teknis jangka panjang | [.docs/adr/](.docs/adr/) |
| *Agent workflow template* (kerangka ini) | `@C:\Users\transcend\.claude\WORKFLOW.md` |
| Aturan *shell tooling* RTK | `@C:\Users\transcend\.codex\RTK.md` |
| **Dokumen utama agen** | **[`AGENTS.md`](AGENTS.md)** |

**Aturan:** Cek AGENTS.md untuk *orchestration* detail sebelum memulai *task* baru.

---

## 2. *Progress — Phase Schedule*

### 2.1 *Roadmap*

```
Phase 0: Docs Readiness + Foundation
  → V1-S1: Provider Health + Data Quality
  → V1-S2: Ticker Lifecycle + Fundamental Snapshot
  → V1-S3: Screener
  → V1-S4: Journal Review + Strategy Rules
  → V1-S5: Polish + Runtime Readiness + UX Stabilization
  → V1-S6: Alerts + Telegram Optional + Earnings Summary
  → Release Readiness: PR review, merge, release
  → V2: Agentic Research Layer (ADR-0018 boundary, ADR-0019 runtime/audit)
        M0 Outbound Brief → M1 Audit Schema → M2 Safe Context
        → M3 Tool Contracts → M4 Hermes Runtime → (M5 Discord, deferred)
  → V3 (horizon, ADR-0020): kemungkinan platform multi-agent/container.
        Boundary-only, TANPA implementasi. Identitas local-first/single-user/
        non-advisory dipertahankan. Tidak mengubah scope V2.
```

### 2.2 *Reusable Phase Gate*

- [x] **Scope:** semua *deliverable* selesai; *scope creep* terdokumentasi sebagai *carry-forward*
- [x] **Build:** Python + web *build zero error*; *typecheck clean*
- [x] **Lint/format:** ruff + prettier *pass*; tidak ada *debug artifacts*; tidak ada `any` tanpa justifikasi
- [x] **Agent handoff:** setiap agen implementasi meninggalkan *handoff note*
- [x] **Tests:** *test* relevan *pass*; regresi terdokumentasi
- [x] **Docs:** AGENTS.md / CLAUDE.md terupdate jika *phase* aktif atau *stack* berubah
- [ ] **Critic review:** *Devil's Advocate review* selesai; alternatif *actionable* terdokumentasi
- [ ] **Phase log:** entri baru di §2.5 dengan *lesson* + *carry-forward*

### 2.3 *Active Phase*

**Phase aktif:** V2 — *Agentic Research Layer / Hermes Runtime (M4)*

**Fokus sprint:** Membangun *runtime* Hermes (`services/hermes`) di atas fondasi yang sudah selesai. **M0–M3 + ADR-0021 (provider config) DONE & committed.** Berikutnya M4 (*gated* — proses *long-running*). Detail task tersisa ada di **§2.6**.

**Selesai (committed di branch `docs/agentic-research-layer-boundary`):**
- ADR-0018 (boundary), ADR-0019 (runtime/audit), ADR-0020 (platform horizon), ADR-0021 (configurable LLM provider)
- M0 — `scripts/agent_brief.py` (pull-only outbound brief, reuse `generate_stock_brief`)
- M1 — migrasi `0008_agent_runtime.sql` (`agent_log`, `agent_write_action`, `research_queue`)
- M2 — `packages/core/agent/` `exposure_summary()` (aggregate-only) + `journal_digest()` (redacted)
- M3 — `packages/core/agent/` tool contracts (`tools.py`) + audit repo (`audit.py`)
- Provider config — `LLMTextProvider`, `OpenAICompatibleProvider`, `resolve_provider()` env-driven; semua scripts pakai factory

**Orchestrator:** *Lead Technical Orchestrator* (lihat AGENTS.md §5)

**Next:** M4 — lihat breakdown **§2.6**. **GATE:** M4 menyalakan proses *long-running* (Telegram *long-polling*); butuh *go-ahead* eksplisit owner sebelum mulai. M5 (Discord) tetap *deferred*.

### 2.4 *Exit Criteria* (V2)

- [ ] M4 sub-task M4.1–M4.8 (§2.6) selesai + tervalidasi
- [ ] *Full Python verification suite pass* (pytest, mypy strict, ruff, ruff-format)
- [ ] Tidak ada bahasa sinyal/*profit*/prediksi di *output* agentic — `validator.scan_banned` di setiap respons *outbound*
- [ ] *Secrets* (Telegram + LLM API key) hanya dari *environment*, tidak pernah di-*render*/di-*commit*
- [ ] *Write action* butuh konfirmasi manual + idempoten (`agent_write_action`); acknowledge/false-positive reuse *lifecycle* V1-S6 (bukan paralel)
- [ ] Hermes reuse `packages/core/ai` + `packages/core/agent` (tanpa rebuild *engine*); tanpa *inbound port*
- [ ] `agent_log` tertulis per interaksi; *ai_log linkage* dipasang
- [ ] *Critic / Devil's Advocate review* selesai
- [ ] Siap *merge* — PR terbuka atau *branch* siap *review owner*

### 2.5 *Phase Log*

| Phase | Status | Lesson | Carry-forward |
|---|---|---|---|
| V1-S0 Docs Readiness | Selesai | *Pre-commit line-ending hook* menyentuh banyak file; *restore noise* dan *commit* hanya docs/*alignment*. | Main di depan origin sampai di-*push*. |
| V1-S1 Provider Health + DQ | Selesai | *Direct path pytest* di sub-*package* kena *import-root quirk*; *full repo pytest* adalah *check* yang andal. | Perhatikan penamaan *freshness* lama saat integrasi S2. |
| V1-S2 Ticker + Fundamentals | Selesai | DuckDB *file lock* saat beberapa CLI baca/tulis paralel. | Jalankan perintah *refresh*/baca secara berurutan. |
| V1-S3 Screener | Selesai | *Direct path pytest* masih bermasalah; *full repo pytest* andal. | *Dogfood* menunggu — *owner opt-in*. |
| V1-S4 Journal + Strategy | Selesai | DB lokal *stale* *break* halaman UI dependen; *runtime bootstrap command* adalah solusinya. | Dogfood V1-S4 menunggu — *owner opt-in*. |
| V1-S4.1 Runtime Lock Harden | Selesai | *Windows cross-process DuckDB contention*, bukan *production leak*. | Prefer *read-only connections* dan *sequential DB-backed fetches*. |
| V1-S5 Polish + Runtime | Selesai | Menjaga *copy* tetap tenang tanpa mengubah *business logic* adalah tantangan utama. | Tidak ada *scope* alerts/Telegram/earnings ditambahkan. |
| V1-S6 Alerts + Telegram + Earnings | Selesai | DuckDB FK *limitation*: harus *update event status* dulu sebelum *insert summary rows*. Telegram tanpa konfigurasi bukan *app failure*. | DB lokal tidak dimigrasi; `scripts.runtime status --json` bersifat *read-only*. |
| V1-S6 Release Readiness / PR Review | Selesai | CRLF = *Windows line-ending noise*, bukan *diff errors*. *Manual smoke test* tetap *owner opt-in*. | Next: buka PR atau jalankan *migration smoke test* yang disetujui *owner*. |
| V2-M1 Audit Schema | Selesai | DuckDB FK butuh urutan insert (parent dulu). `ai_log.id` acak (non-sequential) → linkage presisi butuh wiring runtime. | `agent_log.ai_log_id` *nullable* sampai M4 memasang linkage. |
| V2-M2 Safe Context | Selesai | *Aggregate-only* = kirim rasio bobot, jangan nilai absolut. *Anti-leak test* (sentinel) adalah kunci. | Konsumen = tool contracts M3. |
| V2-M3 Tool Contracts | Selesai | LLM-backed tools ditunda ke M4 (butuh provider wiring + linkage `ai_log_id`). | Pure tools (exposure/journal-digest) sudah audited. |
| V2-M0 Outbound Brief | Selesai | `validator.scan_banned` = sumber kebenaran anti-signal untuk *outbound copy*. Telegram tak terkonfigurasi = print-only, bukan failure. | Script tak punya unit-test langsung (butuh network) — logika murni sudah ter-test. |
| V2 Provider Config (ADR-0021) | Selesai | OpenAI-compat = 1 kelas untuk banyak provider; *structured output* beda per API (tool_use vs function-calling). `detect-secrets` false-positive untuk nama env `*_API_KEY` → pakai pragma allowlist. | M4 construct provider via `resolve_provider()`. Per-provider cost/budget ditunda. |

---

### 2.6 *Remaining Task Breakdown — M4, M5, dst*

> Untuk agent lanjutan (*cold start*). Baca ADR-0018/0019/0020/0021 + AGENTS.md dulu. Semua di branch `docs/agentic-research-layer-boundary`. Pola test: invokasi root `uv run pytest -k ...` (direct-path sub-package gagal). Setiap sub-task = *Definition of Done*: implemented + validated (pytest+mypy strict+ruff) + handoff.

**Aturan M4 yang tidak boleh dilanggar (dari ADR):**
- Reuse `packages/core/ai` (via `resolve_provider()`) + `packages/core/agent` — **jangan** rebuild RAG/response-contract/engine (ADR-0019 D3).
- `services/hermes` boleh import `core`; `core` **tidak** boleh import `services`/`scripts`/`web`.
- Non-advisory: tanpa buy/sell/target/auto-exec; *default read-only*; setiap respons *outbound* lulus `validator.scan_banned`.
- *Secret* (Telegram + LLM) hanya dari `environment`; tidak pernah di-render/commit.
- *Outbound long-polling* saja — **tanpa** inbound port/webhook (ADR-0019 D1).

#### M4 — Hermes Runtime (`services/hermes/`) — GATED (proses long-running)

| Sub | Task | File target | Dependency | Acceptance |
|---|---|---|---|---|
| M4.1 | *Runtime config* env-driven: enable flag, session, Telegram token/chat, provider via `resolve_provider()` | `services/hermes/config.py` | ADR-0021 ✅ | Config dari env; default *disabled* bila unconfigured; tanpa secret ter-render; test |
| M4.2 | *Intent router*: parse command/text → Intent (`brief`,`ticker_snapshot`,`alert_triage`,`journal_capture`,`research_add`,`exposure`,`journal_digest`,`help`,`unknown`) | `services/hermes/intents.py` | M4.1 | Tiap command → intent benar; unknown → fallback aman; unit-test |
| M4.3 | *Policy gate* non-advisory: tolak buy/sell/target/auto-exec; *read-only default*; scan setiap respons | `services/hermes/policy.py` | M4.2 | Intent terlarang ditolak dengan pesan tenang; semua outbound lulus `scan_banned`; test |
| M4.4 | *Read-only tool dispatch*: wire intent → `core/agent` tools (M3) + LLM tools (`generate_stock_brief`/`answer_stock_question` via `resolve_provider()`). **Pasang linkage `ai_log_id`** (item tertunda M3 — perlu `core/ai` mengembalikan log id atau wrapper tipis) | `services/hermes/dispatch.py` | M4.2, M4.3 | Tiap call ter-audit (`agent_log` + `ai_log_id`); respons tervalidasi; reuse M2 boundaries; tanpa akses storage dari surface |
| M4.5 | *Write-action confirmation* idempoten: acknowledge alert + mark false-positive (reuse `alerts/repo` lifecycle V1-S6), save journal draft, add research item (`research_queue`). Flow `pending_confirmation→confirmed→applied` via `agent_write_action` + `idempotency_key` | `services/hermes/writes.py` | M1 ✅, M4.4 | Write butuh konfirmasi eksplisit; duplikat `idempotency_key` ditolak; acknowledge/false-positive lewat lifecycle existing (bukan paralel); journal draft default-only |
| M4.6 | *Telegram long-polling listener*: loop `getUpdates`, dispatch ke router, balas via `send_text_to_telegram`. Offset tracking, graceful stop, single-process | `services/hermes/telegram_listener.py` | M4.2–M4.5 | Start/stop bersih; proses command; secret env-only; tanpa inbound port; test pakai fake transport (tanpa network nyata) |
| M4.7 | *Entrypoint* `uv run -m services.hermes`: baca config, wajib enable eksplisit, status bila unconfigured (bukan failure) | `services/hermes/__main__.py` | M4.1–M4.6 | `python -m services.hermes --help` jalan; disabled-by-default; stoppable |
| M4.8 | *Session/observability*: `session_id`, `agent_log` per interaksi, logging ter-redaksi, cost via `CircuitBreaker` existing | (lintas file) | M4.4 | `agent_log` rows ada; log tak bocor secret; budget terlihat |

**M4 Definition of Done:** semua sub-task done + validated; full suite hijau; `scan_banned` di semua outbound; secret env-only; write idempoten + manual-confirm; reuse `core/ai`+`core/agent`; tanpa inbound port; handoff lengkap.

#### M5 — Discord (DEFERRED)

Prasyarat: nilai Telegram terbukti **dan** kriteria *readiness* Discord (ADR-0018 Q8) didefinisikan dulu. Tasks saat di-*unlock*:
- **M5.1** — ADR kriteria *readiness* Discord + boundary (jawab Q8). Default *private-only*.
- **M5.2** — Discord *gateway* adapter (websocket) reuse intent router/policy/tools M4 (jangan duplikasi).
- **M5.3** — Channel privat threaded (`#research-queue`, `#ticker-*`, dst), weekly digest.
- **Non-goal:** channel publik, sinyal, copy/social trading, advice untuk audience.

#### Sesudah M4/M5 — Sisa V2 & tertunda

- **V2 Release Readiness:** *full verification*, *Critic review*, PR/merge ke `main`, *dogfood* (owner opt-in). Migrasi DB lokal tetap owner opt-in (`uv run python -m scripts.migrate`).
- **Tertunda teknis (ADR-0019/0021):** linkage `ai_log_id` presisi (M4.4), per-provider *cost/budget* config, `response_format: json_schema`, *ticker-level journal opt-in*, *portfolio lot detail* (butuh approval owner), *retention policy* draft chat (`data/private/`).
- **V3 horizon (ADR-0020):** platform multi-agent/container — **hanya** via ADR teknis V3 masa depan; jaga identitas local-first/single-user/non-advisory.

---

## 3. *Stack* (Terkunci)

| Layer | Keputusan |
|---|---|
| Web | Next.js 15 App Router, TypeScript *strict*, Tailwind, shadcn/ui |
| Core | Python 3.11+, *strict typing* |
| Database | DuckDB *file-based* (`data/private/sahamlens.duckdb`) |
| Charts | `lightweight-charts` |
| Tests | `vitest`, `pytest`, `hypothesis` |
| Lint/format | `eslint`, `prettier`, `ruff`, `mypy` |
| *Package managers* | `pnpm`, `uv` |
| AI | *Wrapper* agnostik *provider* di `packages/core/ai` |
| Agent runtime | Proses lokal *long-running* Hermes (`services/hermes`), *outbound long-polling* Telegram; Discord *gateway* menyusul. Lihat ADR-0019. |

Perubahan *stack* butuh ADR eksplisit atau persetujuan *user*.

**Diizinkan oleh ADR-0019 (sebelumnya ditunda):**
- *Long-running service* — **hanya** untuk *runtime* Hermes lokal (*single-user, single-process, outbound long-polling, tanpa inbound port*). Bukan lisensi untuk *service* lain.

**Ditunda (tetap di luar *scope*):**
- FastAPI *sidecar*, *background scheduler* generik, *inbound HTTP server*/*webhook*, *multi-process orchestration*
- *Real-time* atau *intraday alerting*
- Integrasi broker, *account sync*, *order placement*
- *Push notification* di luar Telegram/Discord agentic
- *Cloud sync*, *multi-user auth*, SaaS, *billing*

**Dilarang kecuali di-*override* eksplisit:**
- DSL strategi, *custom scripting*, bahasa sinyal beli/jual/tahan
- Prediksi harga AI
- *Automated IDX scraping/crawling*
- Dependensi yang butuh API *key* berbayar secara *default*

---

## 4. *AI Instructions*

### 4.1 Sebelum Coding

1. Baca AGENTS.md dulu, lalu dokumen relevan dari §1.
2. Cek *active phase* di §2.3 sebelum mulai.
3. Jalankan `rtk git status --short --branch`. Jika WIP tumpang tindih, beri tahu *orchestrator*.
4. Konfirmasi apakah *code scaffolding* benar-benar diminta.
5. Cek *file tree* sebelum membuat file/folder baru.

### 4.2 *Code Rules* (Non-Negotiable)

- *Business logic* di `packages/core`.
- `scripts` hanya *orchestration* (*one-shot CLI*).
- `apps/web` hanya presentasi.
- `services/hermes` adalah *runtime* agentic: *listener*, *routing*, *policy gate*, *write confirmation*. Boleh *import* `packages/core`.
- `packages/core/*` tidak boleh *import* `apps/web/**`, `scripts/**`, atau `services/**`.
- *Agentic layer* (`core/agent` + `services/hermes`) **wajib reuse** `packages/core/ai` (`answer_stock_question`, `generate_stock_brief`, `validator`). Dilarang membangun ulang *RAG context*, *response contract*, atau memanggil *provider* LLM di luar *wrapper* `core/ai` (ADR-0019 D3).
- TypeScript *strict* dan Python *strict typing*.
- Hindari `any` dan `# type: ignore` tanpa alasan singkat.
- Tambah *test* untuk perilaku yang diubah.
- Jangan *commit data private* dari `data/private/*`.
- Prefer PR kecil vertikal.
- Gunakan *conventional commits*.

### 4.3 Anti-Slop

- Jangan klaim selesai sebelum *check* file aktual atau menjalankan verifikasi.
- Jangan tambah *layer* arsitektur baru atau sistem paralel tanpa persetujuan *orchestrator*.
- Jangan tandai fitur selesai tanpa bukti validasi.
- Jangan perkenalkan dependensi baru tanpa persetujuan *orchestrator*.
- Jangan duplikasi logika *evaluator*/klasifier di React atau CLI — *core* pemilik aturan domain.

### 4.4 *Scope Discipline*

Bangun vertikal, bukan horizontal. Satu irisan yang dipoles lebih baik dari beberapa yang setengah jadi.

Urutan bangun:
1. *Data trust* (Provider Health, Data Quality)
2. *Data coverage* (Ticker Lifecycle, Fundamentals)
3. *Screening* (Screener)
4. *Behavior review* (Journal, Strategy Rules)
5. *Polish gate* (Runtime Readiness, UX)
6. *Alert/Earnings lifecycle*

Saat ragu antara spektakel dan kebenaran, prioritaskan kebenaran.

### 4.5 Komunikasi

- Bahasa Indonesia singkat secara *default* kecuali *user* beralih.
- Rujuk ke file dan aturan tepat saat menjelaskan keputusan.
- Saat tidak yakin, berikan 2-3 opsi konkret dengan *trade-off*.
- Tandai konflik awal: perubahan *stack* terkunci, lompatan *phase*, *scope creep*, regresi arah.
- Saat *debugging*: sebutkan apa yang terjadi, apa yang diharapkan, dan bukti.
- Kutip file dengan *path*. Jika data tidak cukup, katakan.

### 4.6 *Contribution Identity*

> **Salin bagian ini verbatim ke setiap AGENTS.md / CLAUDE.md proyek. Jangan dimodifikasi.**

AI adalah *ghostwriter*. Akuntabilitas repositori tetap pada pemilik manusia.

- Jangan tambahkan `Co-Authored-By: Claude` atau *trailer* kointegrasi AI/model lain ke *commit*.
- Jangan tambahkan tag "Generated with Claude Code" atau yang setara ke pesan *commit* atau badan PR.
- Jangan *push commit* dengan identitas penulis AI atau bot.
- Jangan buat AI muncul di grafik kontributor GitHub.
- Identitas penulis dan *committer* harus identitas pemilik repositori manusia yang dikonfigurasi untuk proyek.
- Jika bantuan AI perlu diungkapkan, sebutkan hanya dalam prosa normal di deskripsi PR atau *changelog*, jangan pernah di *metadata git*.

---

## 5. *Implementation Agent Team*

Lihat [`AGENTS.md §5`](AGENTS.md#5-implementation-agent-team) untuk tabel lengkap 11 peran agen.

| # | Peran | Tanggung Jawab Inti |
|---|---|---|
| 1 | **Lead Technical Orchestrator** | Urutan, *scope control*, pembagian tugas, kesiapan *merge*, validasi akhir |
| 2 | **Product / Workflow Architect** | Alur produk, *user journey*, hierarki halaman |
| 3 | **Frontend Engineer** | Implementasi UI, *layout*, *state interaksi*, aksesibilitas |
| 4 | **Backend Engineer** | Rute API, *services*, *storage logic*, integrasi |
| 5 | **Data / Storage Engineer** | Skema, migrasi, aturan persistensi, kompatibilitas mundur |
| 6 | **QA / Validation Engineer** | Rencana *test*, *regression checks*, validasi akhir |
| 7 | **Security / Safety Engineer** | Validasi input, penanganan *secret*, *path traversal* |
| 8 | **Performance / Reliability Engineer** | *Slow paths*, *job handling*, *error recovery* |
| 9 | **Documentation / Handoff Writer** | Catatan *changelog*, ringkasan *sprint*, draf ADR |
| 10 | **Critic / Devil's Advocate** | Tantang asumsi, deteksi *overengineering*, gesekan UX |
| 11 | **Release Captain** | *Checklist gate* akhir, kesiapan *merge*, status siap/tidak |

---

## 6. *Implementation Tracks*

Lihat [`AGENTS.md §6`](AGENTS.md#6-implementation-tracks) untuk detail T0-T9.

| Track | Nama | Pemilik | Tujuan |
|---|---|---|---|
| T0 | Dokumentasi & Source of Truth | Documentation / Handoff Writer | Jaga dokumen tetap selaras |
| T1 | *Product Workflow & UX* | Product / Workflow Architect | Koherensi alur aplikasi |
| T2 | *Frontend Implementation* | Frontend Engineer | *Layout*, komponen, *state* |
| T3 | *Backend / CLI Implementation* | Backend Engineer | CLI, validasi, integrasi |
| T4 | Data, Storage & Migration | Data / Storage Engineer | Keamanan skema, migrasi |
| T5 | AI Provider / Agent Integration | Backend Engineer | Batas *provider*, konfigurasi model |
| T6 | QA, Testing & Regression | QA / Validation Engineer | Validasi *workflow*, cakupan regresi |
| T7 | *Security & Reliability* | Security / Safety Engineer | *Review* keamanan, *secret* |
| T8 | *Performance & Runtime Readiness* | Performance / Reliability Engineer | *Bottleneck*, kendala *runtime* |
| T9 | *Release & Final Gate* | Release Captain | Status akhir, ringkasan perubahan |

---

## 7. *Orchestrator Operating Model*

1. Baca *Documentation Map* dan pahami dokumen yang mengatur *phase* saat ini.
2. Identifikasi *sprint*/phase dari *Progress → Phase Schedule*.
3. Konfirmasi *Stack Locked constraints*.
4. Pecah *task* ke *tracks* implementasi (§6). Tugaskan masing-masing ke agen pemilik.
5. Definisikan *acceptance criteria* untuk setiap *track*.
6. Tugaskan dengan *scope*, kriteria, non-*goal*, dan format *handoff*.
7. Setiap agen harus hasilkan *handoff note* (§8).
8. Jalankan *Critic / Devil's Advocate review* sebelum *gate* akhir.
9. Jalankan QA + Keamanan + validasi Rilis (T6 + T7 + T9) sebelum *merge*.
10. Produksi status akhir: *Done, Partial, Blocked, Deferred,* atau *Risk Accepted*.

**Aturan operasi:** Optimalkan untuk urutan, koherensi, dan reduksi risiko — bukan kerja paralel maksimal.

---

## 8. *Agent Handoff Protocol*

Setiap agen implementasi harus hasilkan *handoff note*. Format:

```
## Handoff: [Nama Peran]

**Agent:** [Nama peran]
**Track:** [T0-T9]
**Scope:** [Apa yang diminta]
**Files/Areas Touched:** [File yang dibuat/dimodifikasi]
**What Changed:** [Ringkasan perubahan]
**What Was Intentionally Not Changed:** [Batas scope yang dihormati]
**Validation Performed:** [Test dijalankan, pemeriksaan manual, bukti]
**Known Risks:** [Yang tidak lengkap, rapuh, atau tidak pasti]
**Recommended Next Agent:** [Agen yang harus lanjut]
**Next Step:** [Satu tindakan berikutnya]
```

**Aturan:** Setiap *handoff* harus tinggalkan konteks yang cukup untuk agen berikutnya tanpa perlu *audit* ulang seluruh repositori.

---

## 9. *Review Gates*

| Gate | Tahap | Pemeriksaan | Kapan | Bisa Dilewati? |
|---|---|---|---|---|
| **A — Scope Confirmation** | Sebelum kerja | Tugas sesuai *sprint*? Agen pemilik jelas? Non-*goal* dinyatakan? Kriteria diterima? | Setiap *task* baru | Tidak |
| **B — Implementation Readiness** | Sebelum coding | File/area terdampak diketahui? *Stack constraints* dihormati? Desain cocok pola yang ada? | Setiap *track implementasi* | Tidak untuk T2-T5; ya untuk T0/T9 |
| **C — Validation** | Setelah implementasi | Test/manual *check* terdokumentasi? Regresi dipertimbangkan? *Edge cases* terdaftar? *Handoff note* ditulis? | Setiap *track* dengan kode/skema | Tidak untuk T2-T8; ya untuk T0 |
| **D — Release Readiness** | Sebelum *merge* | Kerja benar-benar selesai? Kesenjangan diketahui terdokumentasi? *Critic review* selesai? | Setiap *exit phase*/sprint | Tidak |

---

## 10. *Decision Rules*

| Prioritas | Aturan |
|---|---|
| 1 | Prefer **arsitektur yang ada** daripada pola baru. |
| 2 | Prefer **perubahan kecil berurutan** daripada *rewrite* besar. |
| 3 | Prefer **penyelesaian *workflow user*** daripada polesan teknis terisolasi. |
| 4 | Prefer **kepemilikan eksplisit** atas kerja agen anonim. |
| 5 | **Jangan perkenalkan dependensi baru** tanpa persetujuan *orchestrator*. |
| 6 | **Jangan tandai fitur selesai** tanpa bukti validasi. |
| 7 | **Jangan modifikasi *roadmap*, arsitektur, atau *stack constraints* secara diam-diam**. |
| 8 | **Saat ragu, dokumentasikan ketidakpastian** dan usulkan langkah aman terkecil. |

---

## 11. *Recommended Workflow Optimizations*

1. **RACI-*style clarity*** — R: pemilik implementasi, A: Lead Orchestrator, C: Critic/Security/QA, I: Documentation/Release Captain.
2. **Pisahkan peran *builder* dan *reviewer*** — Agen yang sama tidak boleh *reviewer* tunggal karyanya sendiri.
3. **Jadikan *Progress → Phase Schedule* sebagai kebenaran eksekusi** — *Roadmap* = rencana; *schedule* = status.
4. **Tambahkan "Non-Goals" per *sprint*** — Cegah *scope creep*.
5. **Tambahkan "Definition of Done" per *track*** — Selesai = diimplementasi + divalidasi + didokumentasi + di-*handoff*.
6. **Tambahkan "*Risk Register*" per *sprint*** — Maks 5-10 risiko.
7. **"Next Agent Recommendation" bersifat wajib** — Setiap *handoff* harus usul agen lanjutan.

---

## 12. *Final Notes for Future Agents*

1. **File ini adalah sistem operasi proyek.** Baca sebelum perubahan kode apa pun.
2. ***Orchestrator* adalah pintu masukmu.** Jika *scope* tidak jelas, tanya. Jangan improvisasi *scope*.
3. **Kamu spesialis, bukan generalis.** Tandai masalah lintas-batas di *handoff* — jangan perbaiki sendiri.
4. ***Handoff* tidak opsional.** Jika *track* berakhir tanpa *handoff note*, kerja tidak lengkap.
5. **Validasi tidak opsional.** Jika *track* berakhir tanpa bukti berfungsi, kerja tidak lengkap.
6. ***Scope* adalah musuh kualitas.** Tandai *scope* terlalu besar ke *orchestrator* segera.
7. **Baca dokumen sebelum kode.** Jika dokumen kontradiksi kode, tandai kontradiksinya.
8. ***Critic* adalah temanmu.** Sambut *review*. Libatkan alternatif.
9. **Satu PR = satu urusan.** Jangan gabung *refactor* dengan fitur.
10. ***Git history* adalah catatan permanen.** Tulis *commit message* jelas. Jangan *force-push branch* bersama.

---

## *Scope Guardrails*

**Pekerjaan V1 yang diizinkan:**
- Data Quality Dashboard
- Provider Health
- *Ticker lifecycle* dan *coverage*
- *Fundamental Snapshot* dengan kelengkapan/kepercayaan diri
- *Screener* dengan bahasa tanpa sinyal transparan
- Aturan/kejadian *alert* lokal dengan *feedback false-positive*
- *Weekly Journal Review*
- *Simple Strategy Rules*
- *Earnings Summary manual-first*

**Di luar *scope* V1:**
- Login broker, *cookies, sessions, account sync*, atau *order placement*
- Janji *realtime* atau *tick-data*
- AI prediktif, *alert* AI beli/jual, atau *forecasting alerts*
- Rekomendasi publik, penjualan sinyal, SaaS, *auth*, *billing*, atau *multi-user*
- *Automated IDX crawling*
- Penyimpanan/republikasi berita lengkap
- DSL Strategi

---

## *Repo Mental Model*

```
apps/web/          Next.js dashboard
packages/core/     Python data core
  data_sources     provider dan metadata sumber
  data_quality     provider health, freshness, coverage
  fundamentals     snapshot, completeness, confidence
  screener         aturan dan hasil transparan
  alerts           aturan lokal, event, feedback
  earnings         metadata earnings manual-first
  journal          entri dan weekly review
  strategy         aturan sederhana, tanpa DSL
  runtime          readiness, schema status, bootstrap contract
  ai               LLM wrapper dan validasi
  agent            tool contracts, safe context, intent (pure, reuse ai)
  schemas          Model Pydantic dan migrasi
services/          runtime long-running (import core, bukan sebaliknya)
  hermes           listener long-polling, routing, policy gate, write confirm
scripts/           CLI orchestration (one-shot)
data/sample/       data palsu yang di-commit
data/private/      data lokal asli yang diabaikan
prompts/system/    template prompt berversi
config/            contoh config di-commit, lokal diabaikan
.docs/             dokumentasi kanonis
```

---

*CLAUDE.md mengikuti template WORKFLOW.md global di `@C:\Users\transcend\.claude\WORKFLOW.md` dan terhubung dengan [`AGENTS.md`](AGENTS.md) sebagai dokumen induk.*
