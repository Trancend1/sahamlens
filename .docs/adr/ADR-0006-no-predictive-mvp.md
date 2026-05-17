# ADR-0006 — Tidak Ada Predictive AI di MVP

- **Status:** accepted (governance)
- **Date:** 2026-05-16
- **Deciders:** owner

## Context

Predictive AI (Prophet, LSTM, transformer) untuk forecasting harga sering jadi feature "wow" di tool trading. Tapi:
- IDX noisy, illiquid (di luar top 50), event-driven.
- Pola historis sering pecah karena news / kebijakan / earnings.
- Pemula cenderung over-trust output chart yang kelihatan scientific.
- Output gampang overfit tanpa edge nyata.

Pertanyaan: apakah build di MVP?

## Decision

**Tidak.** Predictive AI **dilarang** di MVP. Boleh masuk Phase V2+ **sebagai experimental**, terisolasi dari decision support core (lihat [PRD_clean.md §5.3](../PRD_clean.md)).

## Consequences

**Positive:**
- Owner tidak terjebak false confidence dari "AI forecast".
- Effort difokuskan ke fondasi: indicator literacy, journal discipline, risk management.
- Tidak menumpuk maintenance untuk model yang belum proven.
- Mencegah tool jadi "crystal ball" yang melawan philosophy (lihat [TRADING_DISCLAIMER.md](../TRADING_DISCLAIMER.md)).

**Negative:**
- Tidak ada "predicted price" badge yang user request.
- Beberapa learning opportunity tertunda (memahami time-series ML).

**Trigger untuk re-evaluate (paling cepat V2):**
- Journal discipline established (≥ 3 bulan konsisten review).
- Backtest framework sudah ada untuk validasi hipotesis fair.
- Owner paham overfitting, walk-forward validation, naive baseline.
- Visualisasi probability band dengan caveat siap.

Bahkan saat re-evaluate: predictive AI **hanya** boleh sebagai visualisasi riset, **bukan** signal. Target price absolut & entry/exit instruction tetap terlarang permanen.

## Alternatives Considered

1. **Build dengan caveat besar di-UI** — di-reject: caveat tidak menetralisir bias kognitif. Output yang ada di-screen akan dianggap signal terlepas dari label.
2. **Build sebagai notebook only (`notebooks/experiments/`)** — accepted untuk research, **tidak** terintegrasi ke dashboard.

## Related

- [PRD_clean.md §5.3, §10](../PRD_clean.md)
- [AI_BOUNDARIES.md §2.3](../AI_BOUNDARIES.md)
- [TRADING_DISCLAIMER.md](../TRADING_DISCLAIMER.md)
