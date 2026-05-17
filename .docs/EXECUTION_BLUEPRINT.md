# EXECUTION_BLUEPRINT — SahamLens

**Source of truth for:** Implementation phases, sprint breakdown, MVP exit criteria, feature rollout sequence, practical execution checklist.
**Tidak di sini:** Product scope (→ [PRD_clean.md](PRD_clean.md)), tech stack (→ [ARCHITECTURE.md](ARCHITECTURE.md)), code style (→ [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md)).

**Versi:** 1.0
**Status:** Active — **update tiap sprint review**

---

## 1. Execution Philosophy

1. **Vertical slice over horizontal layer.** Tiap milestone deliverable end-to-end (data → calc → UI → AI), bukan "selesaikan semua data layer dulu".
2. **MVP = small + sharp.** Kalau feature tidak bantu owner mengambil keputusan lebih jernih → tunda.
3. **Test-first untuk financial calc.** Semua formula keuangan ditulis test dulu (→ [ENGINEERING_STANDARDS.md §5](ENGINEERING_STANDARDS.md)).
4. **Demo to self.** Setiap akhir sprint, owner pakai produk untuk daily review nyata. Kalau tidak dipakai → revisit prioritas.

---

## 2. Phase Map

```
Phase 0  →  Phase MVP  →  Phase V1  →  Phase V2  ─┐
                                                   │
Phase Experimental (paralel, terisolasi) ─────────┘
```

| Phase | Target durasi | Tujuan |
|---|---|---|
| **Phase 0 — Foundations** | 1–2 minggu | Repo skeleton, tooling, security baseline |
| **Phase MVP — Private Learning Dashboard** | 6–10 minggu | Watchlist + indicator + journal + AI brief + risk |
| **Phase V1 — Better Decision Support** | +6–8 minggu | Fundamental + screener + alerts + earnings summary |
| **Phase V2 — Personal Trading System Builder** | open-ended | Playbook + backtest + analytics + paper trading + PWA |
| **Phase Experimental** | paralel | Forecasting lab, sentiment lab, pattern recog — isolated |

---

## 3. Phase 0 — Foundations (Sprint 0)

### Deliverable
- Repo structure (lihat [ENGINEERING_STANDARDS.md §2](ENGINEERING_STANDARDS.md)).
- `.gitignore`, `.env.example`, pre-commit hooks, gitleaks.
- CI workflow (lint + test + secret scan).
- DuckDB skeleton + first migration.
- `DISCLAIMER.md`, `README.md`, `.docs/` populated.
- `CLAUDE.md` di root.
- Next.js 15 app shell (single page hello world) + Tailwind + shadcn/ui init.
- Python data core scaffold + first dummy script.
- Sample data committed (fake portfolio, fake journal).

### Exit
- `pnpm dev` jalan, render hello.
- `pytest` & `vitest` jalan tanpa error.
- Pre-commit hook block dummy secret commit (verified manual).
- CI hijau di PR test.

---

## 4. Phase MVP — Private Learning Dashboard

Target: **6–10 minggu santai, solo, semi-vibe**.

### 4.1 Sprint breakdown (indikatif)

| Sprint | Fokus | Deliverable utama |
|---|---|---|
| **S1** | Data ingestion + DuckDB | `ingest_prices.py` (yfinance → DuckDB), watchlist CRUD, sample 10 ticker |
| **S2** | Indicator engine | MA 5/10/15/50/200, volume avg, RSI 14, MACD — semua test ≥90% coverage |
| **S3** | Stock detail page + chart | Next.js page render OHLCV + indicator overlay (lightweight-charts) + `IndicatorCard` 5-block |
| **S4** | News ingestion + AI summarizer | RSS adapter, LLM wrapper, news summary di stock detail |
| **S5** | Trade journal + risk checklist | Form, validation, position size calc (test + property-based) |
| **S6** | Daily brief + AI chat assistant | `generate_brief.py`, AI chat panel dengan RAG context |
| **S7** | Freshness UX + polish + portfolio import | `<FreshnessBadge />`, CSV import, footer disclaimer, cooling-off prompt |
| **S8** (buffer) | Hardening + demo to self | Bug fix, owner pakai untuk daily review nyata 5 hari berturut-turut |

### 4.2 Exit criteria (semua wajib)

Produk:
- [ ] Owner bisa review watchlist dalam 15–30 menit.
- [ ] Owner bisa buat trade plan lengkap (semua field §6.2 PRD).
- [ ] AI output **selalu** cite data + tampilkan caveat (→ [AI_BOUNDARIES.md §3](AI_BOUNDARIES.md)).

Teknis:
- [ ] Tidak ada private data ter-commit (verified by pre-commit + CI `no_private_leak`).
- [ ] Core indicator calculation test coverage ≥ 90%.
- [ ] Position size calculator: ≥ 5 unit test + property-based.
- [ ] Banned-phrase filter aktif di AI pipeline.
- [ ] Schema validation reject malformed AI output.

Safety:
- [ ] Disclaimer di README, UI footer, AI panel, export.
- [ ] Tidak ada bahasa command buy/sell di copy.

---

## 5. Phase V1 — Better Decision Support

### Scope

- Fundamental snapshot (PER, PBV, ROE, DER, EPS, dividend yield).
- Custom watchlist tag & multi-list.
- Simple screener (rule kombinasi indikator + fundamental).
- Alert rule + Telegram notification.
- Earnings / financial report summarizer.
- Weekly journal review.
- CSV import Stockbit lebih lengkap.
- Data quality dashboard (freshness + fetch error rate per source).

### Exit
- Bisa filter kandidat by basic technical + fundamental criteria.
- Bisa review behavior mingguan & rule violation.
- Alert berguna; false-positive rate dilacak & < 30%.

---

## 6. Phase V2 — Personal Trading System Builder

### Scope

- Strategy playbook (encode setup pribadi).
- Backtesting-lite untuk rule sederhana.
- Performance analytics by setup type.
- Paper trading simulator.
- Local semantic search atas journal & note (vector DB boleh masuk di sini — jangan sebelumnya).
- PWA / mobile-friendly dashboard.
- (Opsional) migrasi PostgreSQL kalau data growth justified.

### Exit
- Owner bisa mengukur setup mana yang berkinerja.
- Backtest disertai caveat realistis (no overfitting claim).
- Journal history searchable.

---

## 7. Phase Experimental (Paralel)

Dijalankan kalau ada momentum belajar, **tidak** memblokir roadmap utama.

| Lab | Deliverable |
|---|---|
| Forecasting research lab | Notebook Prophet / simple LSTM dengan naive baseline comparison |
| Social sentiment lab | Noisy dataset analysis, **no** integrasi ke decision support |
| Chart pattern recognition lab | Educational only, label experimental |
| LLM-assisted strategy critique | Manual review per output, caveats eksplisit |
| Local model experimentation | Self-hosted small model untuk privacy-sensitive task |

Output experimental **wajib terpisah visual** dari decision support. Tidak pernah jadi instruksi trade.

---

## 8. Sprint Cadence

- **Sprint length:** 1 minggu (solo). Bisa di-extend ke 2 minggu kalau life happens — tidak ada SLA.
- **Sprint review (self):** 30 menit. Pakai produk untuk daily review nyata. Catat friction.
- **Refactor sprint:** setiap sprint ke-3 dialokasikan untuk konsolidasi tech debt (lihat [ENGINEERING_STANDARDS.md §10](ENGINEERING_STANDARDS.md)).

---

## 9. Definition of Done (per task)

Sebuah task selesai kalau:
- [ ] Test ditulis & passing (untuk financial calc: coverage ≥90%).
- [ ] Lint + type check clean.
- [ ] Tidak melanggar boundary (AI, security, data).
- [ ] Dokumentasi update kalau ada perubahan di public API atau schema.
- [ ] ADR ditulis kalau ada keputusan teknis baru.
- [ ] Pre-commit hooks pass.
- [ ] Manual smoke test di UI (kalau menyentuh UI).
- [ ] Commit message Conventional Commits.

---

## 10. Kill Switches (referenced)

Lihat [PRD_clean.md §10](PRD_clean.md). Operational triggers:
- Sprint ke-3 berturut-turut tidak ship deliverable apa pun → review apakah masih relevan.
- Owner skip daily review > 2 minggu → freeze dev, audit fit.
- Cost LLM bulan berjalan > Rp 500rb → matikan AI panel non-essential.

---

## 11. Risk Register

| Risk | Likelihood | Impact | Mitigasi |
|---|---|---|---|
| Source data break / change | High | Medium | Adapter layer + multi-source fallback ([DATA_SOURCES.md §6](DATA_SOURCES.md)) |
| LLM cost overrun | Medium | Medium | Model routing, monthly cap, circuit breaker |
| Owner over-rely ke AI → loss | Medium | High | UX dorong critical thinking + cooling-off |
| Tech debt menumpuk | High | Medium | Refactor sprint per 3 sprint |
| Privacy leak ke repo publik | Medium | High | `.gitignore` + pre-commit + CI scan |
| Bug pada position size calc | Low | High | Coverage ≥ 90% + property-based test |
| Scope creep balik ke "SaaS" | Medium | Medium | PRD_clean + governance docs sebagai constitution |
| Owner berhenti trading | Medium | — | Valid kill criteria, bukan risk |
| ToS violation source | Medium | Medium | Source resmi, dokumentasi, hindari aggressive scrape |
| Burnout owner | Medium | High | Kill criteria eksplisit; tidak ada kewajiban user lain |

---

## 12. Output Documents Status

| Document | Status | Owner |
|---|---|---|
| [PRD_clean.md](PRD_clean.md) | ✅ done | self |
| [ARCHITECTURE.md](ARCHITECTURE.md) | ✅ done | self |
| [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | ✅ done | self |
| [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) | ✅ done | self |
| [DATA_SOURCES.md](DATA_SOURCES.md) | ✅ done | self |
| [AI_BOUNDARIES.md](AI_BOUNDARIES.md) | ✅ done | self |
| [SECURITY.md](SECURITY.md) | ✅ done | self |
| [TRADING_DISCLAIMER.md](TRADING_DISCLAIMER.md) | ✅ done | self |
| [CONTRIBUTING.md](CONTRIBUTING.md) | ✅ done | self |
| [adr/](adr/) | seeded (8 ADRs) | self |
| Sprint plan detail | pending — di-generate per sprint | self |
| `CLAUDE.md` (root) | ✅ done | self |
