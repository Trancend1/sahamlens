# SECURITY — SahamLens

**Source of truth for:** Privacy model, threat model, secret management, public-repo rules, controls list, AI privacy boundary, incident response.
**Tidak di sini:** AI behavior rules (→ [AI_BOUNDARIES.md](AI_BOUNDARIES.md)), data source ToS (→ [DATA_SOURCES.md](DATA_SOURCES.md)), legal positioning (→ [TRADING_DISCLAIMER.md](TRADING_DISCLAIMER.md)).

**Versi:** 1.0
**Status:** Active — **governance, mengikat semua kode**

---

## 1. Privacy Model

### Default classification

| Asset | Classification | Storage rule |
|---|---|---|
| Portfolio data | **Sensitive** | `data/private/` (gitignored), tidak ke cloud DB default |
| Trade journal | **Sensitive** | `data/private/` (gitignored) |
| Strategy rules (nilai konkret) | **Sensitive** | `config/*.yml` (gitignored), template di `*.example.yml` (committed) |
| API keys | **Secret** | `.env.local` (gitignored) |
| Watchlist personal | **Sensitive (mild)** | `data/private/` |
| Source code | Public | Repo |
| Prompt templates (tanpa data privat) | Public | Repo |
| Sample data | Public (fake only) | `data/sample/` |
| AI audit log | Sensitive (local only) | `data/private/` (di DuckDB) |

**Aturan singkat:** kalau bocor bikin owner malu atau rugi, → Sensitive. Kalau bisa dipakai third-party menyamar jadi owner, → Secret.

---

## 2. Threat Model

### 2.1 In-scope threats

| Threat | Likelihood | Impact | Mitigasi utama |
|---|---|---|---|
| Accidental commit data privat ke repo publik | Medium | High | `.gitignore` strict + pre-commit hook + CI `no_private_leak` |
| API key bocor (commit, paste, log) | Low–Medium | Medium | `.env.local` only + `gitleaks` di pre-commit & CI |
| LLM provider kirim data privat ke pihak ketiga | Medium | Medium | Redaction layer di context builder ([AI_BOUNDARIES.md §7](AI_BOUNDARIES.md)) + opt-in untuk journal context |
| ToS violation source data | Medium | Medium | Pakai source resmi, dokumentasikan, hindari aggressive scraping ([DATA_SOURCES.md](DATA_SOURCES.md)) |
| Over-trust AI → loss | Medium | High | UX yang dorong critical thinking + disclaimer ([DESIGN_SYSTEM.md](DESIGN_SYSTEM.md), [TRADING_DISCLAIMER.md](TRADING_DISCLAIMER.md)) |
| Local laptop dicuri / hilang | Low | High | Disk encryption owner-managed (BitLocker / FileVault); backup encrypted ke private storage |
| Supply-chain (dependency compromise) | Low | Medium | Pin versions + `pnpm audit` / `pip-audit` di CI |
| Source endpoint berubah → fetch silent fail | High | Medium | Schema validation + freshness badge wajib visible |
| Tech debt accumulation | High | Low-Medium | Refactor sprint per 3 sprint ([ENGINEERING_STANDARDS.md §10](ENGINEERING_STANDARDS.md)) |

### 2.2 Out-of-scope

- Nation-state targeted attack (single-user personal tool).
- DDoS pada self-hosted dashboard (lokal, tidak ada).
- Multi-user authorization (no multi-user, lihat [PRD_clean.md](PRD_clean.md)).
- HIPAA/GDPR/PCI compliance (no third-party PII, no payments).

---

## 3. Required Controls

### 3.1 `.gitignore` (wajib include)

```gitignore
# secrets
.env
.env.*
!.env.example

# private data
data/private/**
!data/private/.gitkeep

# private config
config/*.yml
!config/*.example.yml

# build / cache
node_modules/
.next/
.turbo/
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.mypy_cache/

# OS
.DS_Store
Thumbs.db
```

### 3.2 Pre-commit hooks (`.pre-commit-config.yaml`)

Wajib:
- `gitleaks` — scan secret patterns.
- Custom `no_private_leak` — fail kalau diff menyentuh `data/private/**` atau `config/*.yml` non-example.
- `detect-secrets` (opsional, second layer).
- Lint + format (ruff, prettier, eslint).

### 3.3 CI checks (GitHub Actions)

- Re-run `gitleaks` (defense in depth).
- Test `tests/test_no_private_leak.py` — gagal kalau path `data/private/**` muncul di diff.
- `pnpm audit` (high+ severity) + `pip-audit`.
- Lint + type check + unit test (→ [ENGINEERING_STANDARDS.md §7](ENGINEERING_STANDARDS.md)).

### 3.4 Local secrets

- File: `.env.local` (gitignored). Template: `.env.example` (committed dengan placeholder).
- Loaded via `dotenv` (Next.js native) / `python-dotenv`.
- **Tidak pernah** log nilai secret. Sanitize logger formatter untuk strip pattern `*_KEY|*_TOKEN|*_SECRET`.
- Rotation: kalau ada suspicion bocor → rotate immediately, rebuild local config, `git filter-repo` kalau perlu remove dari history.

### 3.5 Data export & deletion

- `scripts/backup_private_data.py` — encrypted dump (e.g. `age` atau `openssl enc`) ke path user-specified. Tidak default ke cloud.
- `scripts/wipe_private_data.py` — single command untuk hapus `data/private/**` setelah confirmation prompt.

---

## 4. AI Privacy Boundary

(Mirror dari [AI_BOUNDARIES.md §7](AI_BOUNDARIES.md), di sini untuk security context.)

Sebelum context dikirim ke LLM provider:
- Redaction layer di `packages/core/ai/redactor.py`.
- Strip: account number, broker ID, full names, addresses.
- Portfolio: kirim aggregate (sektor exposure), bukan avg price + lots detail (kecuali eksplisit opt-in per query).
- Journal: default tidak dikirim. Owner harus toggle "Include journal context" per chat session.
- Logging context: lokal only (`ai_log` table), tidak shared ke telemetry vendor.

Catatan provider:
- Anthropic API tidak training on user data (per ToS saat dokumen ditulis). **Tetap** redact sebagai defense in depth.
- Kalau ganti provider, review ulang ToS sebelum routing data sensitive (→ [ADR-0005](adr/ADR-0005-llm-wrapper.md)).

---

## 5. Public Repo Rules

### 5.1 Boleh ada di repo publik
- Source code (Python + TypeScript).
- Dokumentasi (`.docs/`).
- Sample data fake (`data/sample/`).
- Fake journal example.
- Setup guide.
- Architecture notes & ADR.
- Prompt templates **tanpa** data privat.

### 5.2 Tidak boleh
- Portofolio nyata.
- Trade history nyata.
- Screenshot broker dengan data akun.
- API key apa pun.
- Prompt LLM yang berisi note pribadi.
- Cached news / scraped content yang melanggar ToS source.
- Backup file `data/private/**`.

### 5.3 Sample data rules
- Ticker boleh asli (BBCA.JK, dll — public data).
- Portfolio + journal sample wajib **fake**: jumlah modal, harga, P&L. Beri header komentar `# SAMPLE — NOT REAL TRADING DATA`.

---

## 6. Incident Response (Lightweight)

Single-user system, tapi tetap perlu prosedur.

### 6.1 Suspected secret leak
1. Rotate secret immediately (API console).
2. `git log -p -- .env.local` cek apakah pernah ter-commit.
3. Kalau pernah: `git filter-repo` untuk hapus dari history.
4. Force-push (warn: destructive; pastikan tidak ada collaborator pending) atau buat repo baru.
5. Update `.env.example` kalau ada field baru.
6. Catat di `docs/incidents/YYYY-MM-DD-secret-leak.md` (lokal, tidak commit).

### 6.2 Suspected private-data leak
1. Identifikasi file & commit.
2. `git filter-repo` untuk hapus.
3. Force-push setelah confirm.
4. Audit `.gitignore` — kenapa file lolos? Tambah pattern.
5. Tambah test regression di `tests/test_no_private_leak.py`.

### 6.3 Bug yang menyebabkan rugi finansial
Mirror kill criteria di [PRD_clean.md §10](PRD_clean.md):
1. Freeze development.
2. Root-cause analysis.
3. Perbaiki + regression test.
4. Tulis ADR atau post-mortem (lokal).
5. Resume hanya setelah test menutup case.

---

## 7. Dependency Hygiene

- Pin major versions di `package.json` / `pyproject.toml`.
- Lockfile committed (`pnpm-lock.yaml`, `uv.lock`).
- `pnpm audit` (high+) & `pip-audit` weekly via CI.
- Tidak install dependency dari untrusted source (no `npm install` random gist URL).
- Sebelum tambah dep baru: cek age, maintainer activity, weekly download. Lihat [ENGINEERING_STANDARDS.md §8](ENGINEERING_STANDARDS.md).

---

## 8. Network & Hosting

### MVP
- Tidak ada inbound port terbuka ke internet (lokal only).
- Outbound: HTTPS ke yfinance, RSS feeds, LLM provider, optional Telegram. Dokumentasikan di firewall allowlist kalau owner pakai egress filter.

### Hosted dashboard (opsional V1+)
- Hosted via Vercel **tanpa data privat** (read-only mirror). Kalau dipasang:
  - Auth wajib (Vercel password protection minimum, atau Cloudflare Access).
  - Data privat tidak ke Vercel storage; data via tunnel (tailscale/cloudflared) ke local DB.
  - HTTPS enforced.

---

## 9. Security Review Checklist (Sebelum Major Release)

- [ ] `.gitignore` masih cover semua sensitive path.
- [ ] Pre-commit hook jalan & gitleaks tidak findings.
- [ ] Tidak ada secret di env var commit history.
- [ ] AI redactor cover field baru kalau ada schema journal/portfolio berubah.
- [ ] CI `no_private_leak` test pass.
- [ ] Dependency audit clean (high+ severity).
- [ ] Banned-phrase filter masih relevan dengan prompt terbaru ([AI_BOUNDARIES.md §4.4](AI_BOUNDARIES.md)).
