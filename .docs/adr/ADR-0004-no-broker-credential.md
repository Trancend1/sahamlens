# ADR-0004 — Tidak Ada Broker Credential Storage

- **Status:** accepted (governance — sulit di-revisit)
- **Date:** 2026-05-16
- **Deciders:** owner

## Context

Otomatisasi data portfolio bisa dilakukan dengan menyimpan kredensial broker (Stockbit, Mirae, dll) lalu auto-login + scrape posisi terkini. Beberapa tool retail melakukan ini.

Pertanyaan: apakah sistem perlu store broker credential?

## Decision

**Tidak.** SahamLens **tidak pernah** menyimpan broker credential, cookie, session token, atau OAuth token. Semua data portfolio masuk via:
- Manual entry di UI.
- CSV import dari export resmi broker (user-initiated).
- Screenshot / note (tidak parsed).

## Consequences

**Positive:**
- Tidak ada attack surface untuk credential theft.
- Tidak ada risiko legal / ToS violation broker.
- Tidak ada risiko sistem auto-execute order kalau kompromise.
- Tidak ada risiko owner "membiasakan" sistem menyentuh akun trading.
- Removes entire class of feature requests (auto-trade, auto-rebalance) by design.

**Negative:**
- Friction: owner harus manual update portfolio setelah trade.
- Tidak ada real-time P&L sync.
- Tidak ada auto-detection drift portfolio.

**Trigger untuk re-evaluate:**
- **Tidak ada.** Ini governance decision. Re-evaluate butuh PR + ADR baru + konfirmasi tetap fit personal-use scope.

## Alternatives Considered

1. **Encrypted credential vault** — di-reject: tetap satu titik failure besar; kalau encryption key bocor, semua kredensial open. Risk:benefit tidak proportional.
2. **OAuth broker (kalau ada)** — di-reject: belum ada OAuth resmi dari broker IDX major saat dokumen ditulis; re-evaluate kalau muncul.
3. **Browser extension scrape session** — di-reject: ToS violation, brittle, melatih owner mengandalkan automation untuk task yang seharusnya manual.

## Related

- [SECURITY.md §1, §3](../SECURITY.md) — privacy model.
- [AI_BOUNDARIES.md §9](../AI_BOUNDARIES.md) — no automated trade execution.
- [PRD_clean.md §4.4](../PRD_clean.md) — excluded features.
