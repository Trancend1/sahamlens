# SahamLens — Documentation Index

**Versi:** 1.1
**Tanggal:** 2026-05-18
**Bahasa:** Indonesian (primary). Lihat [ADR-0007](adr/ADR-0007-doc-language.md).

Dokumentasi modular dengan ownership boundary jelas. Setiap dokumen punya **satu** tanggung jawab; informasi tidak diduplikasi antar dokumen — gunakan referensi silang.

---

## Documentation Map

| Tier | Dokumen | Tanggung Jawab Utama (Single Source of Truth) |
|---|---|---|
| **Governance** | [PRD.md](PRD.md) | Product scope, goals, non-goals, success metrics, product policy |
| **Governance** | [AI_BOUNDARIES.md](AI_BOUNDARIES.md) | Apa AI boleh & tidak boleh; output schema; hallucination prevention |
| **Governance** | [SECURITY.md](SECURITY.md) | Privacy model, threat model, secret handling, repo public rules |
| **Governance** | [TRADING_DISCLAIMER.md](TRADING_DISCLAIMER.md) | Legal positioning, disclaimer text, financial-risk boundary |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) | System design, module boundaries, data flow, tech stack |
| **Architecture** | [DATA_SOURCES.md](DATA_SOURCES.md) | Source catalog, reliability, rate limits, freshness policy |
| **Architecture** | [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | UI philosophy, beginner-safe patterns, indicator display rule |
| **Engineering** | [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) | Code style, git, test, lint, naming, folder structure |
| **Engineering** | [CONTRIBUTING.md](CONTRIBUTING.md) | Kontribusi tanpa mengubah arah personal-use |
| **Execution** | [EXECUTION_BLUEPRINT.md](EXECUTION_BLUEPRINT.md) | Roadmap MVP→V2, sprint breakdown, exit criteria |
| **Decisions** | [adr/](adr/) | Architecture Decision Records (append-only) |

`CLAUDE.md` (di root repo) **bukan** dokumen ini. Ia AI alignment & workflow layer — pointer ke dokumen di sini, bukan duplikat isi.

---

## Dependency Hierarchy

```
                    ┌──────────────────┐
                    │      PRD.md      │  (top — semua doc derive dari ini)
                    └────────┬─────────┘
            ┌────────────────┼────────────────┬─────────────────┐
            ▼                ▼                ▼                 ▼
   ┌───────────────┐ ┌──────────────┐ ┌────────────────┐ ┌────────────────────┐
   │ AI_BOUNDARIES │ │  SECURITY    │ │  ARCHITECTURE  │ │ TRADING_DISCLAIMER │
   └───────┬───────┘ └──────┬───────┘ └────────┬───────┘ └────────────────────┘
           │                │                  │
           │                │       ┌──────────┼──────────┐
           │                │       ▼          ▼          ▼
           │                │  ┌─────────┐ ┌────────┐ ┌──────────────┐
           │                │  │ DESIGN  │ │ DATA   │ │ ENGINEERING  │
           │                │  │ SYSTEM  │ │ SOURCES│ │ STANDARDS    │
           │                │  └─────────┘ └────────┘ └──────┬───────┘
           │                │                                 │
           └────────────────┴─────────────────┬───────────────┴───────┐
                                              ▼                       ▼
                                  ┌────────────────────┐    ┌──────────────────┐
                                  │ EXECUTION_BLUEPRINT│    │  CONTRIBUTING    │
                                  └────────────────────┘    └──────────────────┘

   ADRs (adr/*.md) — append-only audit trail untuk semua keputusan teknis besar.
```

**Aturan baca:** Hierarki atas → bawah. Dokumen bawah boleh reference ke atas, tidak sebaliknya. Kalau bawah perlu mempengaruhi atas, buka PR + tulis ADR baru.

---

## Document Roles

- **Source of Truth** — satu-satunya tempat fakta itu didefinisikan. Edit di sini.
- **Supporting Document** — menggunakan fakta dari source-of-truth. Cite, jangan copy.
- **Implementation Reference** — petunjuk teknis untuk eksekusi (EXECUTION_BLUEPRINT, ENGINEERING_STANDARDS).
- **Governance Document** — kebijakan yang membatasi semua keputusan lain (PRD, AI_BOUNDARIES, SECURITY, TRADING_DISCLAIMER).

---

## Single Source of Truth Rules

1. **Sebelum menulis fakta baru:** cari apakah sudah ada di dokumen lain. Kalau ada → cite + link.
2. **Sebelum mengubah fakta:** edit hanya di source-of-truth.
3. **Sebelum menambahkan dokumen baru:** cek apakah konten muat di dokumen existing. Bias kuat ke **tidak menambah file**.
4. **Saat fakta di dua tempat divergen:** source-of-truth menang.
5. **Semua keputusan teknis besar** → ADR.

---

## Anti-Patterns

- Menulis ulang konten PRD.md di ARCHITECTURE.md.
- Menyembunyikan keputusan teknis di README/commit message; harusnya di ADR.
- Membuat dokumen "Overview"/"Summary" — itu pekerjaan README ini.
- Enterprise governance theater (RACI, stakeholder map) untuk single-user project.
- Auto-generated docs yang tidak dibaca.

---

## ADR Strategy

- **Format:** [MADR](https://adr.github.io/madr/) singkat. Status: `proposed | accepted | deprecated | superseded`.
- **Penomoran:** sequential 4 digit (`ADR-0001`...). Tidak di-renumber.
- **Tulis ADR untuk:** library/framework yang sulit di-swap, boundary arsitektur, kebijakan keamanan/AI, penolakan fitur yang sering direquest.
- **Tidak perlu ADR untuk:** keputusan style (→ ENGINEERING_STANDARDS), ephemeral (→ EXECUTION_BLUEPRINT).
- **Lifecycle:** ADR superseded tetap ada. Tambahkan `Superseded by: ADR-XXXX` di header.

---

## Optimisasi target

1. Solo developer cepat onboard kembali setelah 2 minggu rehat.
2. AI assistant (Claude Code) bisa load CLAUDE.md + 1 dokumen relevan untuk task tertentu.
3. Public contributor paham scope tanpa harus baca PRD legacy.
4. Iterasi cepat — ubah satu fakta = satu file.
