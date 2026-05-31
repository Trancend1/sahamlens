# SahamLens Documentation

Dokumentasi ini adalah source of truth untuk SahamLens: personal trading companion untuk satu trader retail IDX. Tujuan utama V1 adalah better decision support, bukan rekomendasi publik, bukan signal seller, bukan broker automation.

## Read Order

Untuk mulai implementasi V1, baca dalam urutan ini:

1. [PRD.md](PRD.md) - scope produk, non-goals, dan batas V1.
2. [EXECUTION_BLUEPRINT.md](EXECUTION_BLUEPRINT.md) - roadmap, sprint, backlog, dan gate eksekusi.
3. [ARCHITECTURE.md](ARCHITECTURE.md) - desain sistem, modul, schema area, CLI, API, UI.
4. [DATA_SOURCES.md](DATA_SOURCES.md) - provider, freshness, coverage, confidence, dan batas data.
5. [AI_BOUNDARIES.md](AI_BOUNDARIES.md) - aturan AI dan safety output.
6. [SECURITY.md](SECURITY.md) - privasi, secrets, dan threat model.
7. [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) - test, lint, git, dependency, dan PR rules.

## Source of Truth Map

| Topic | Canonical file |
|---|---|
| Product scope, goals, non-goals | [PRD.md](PRD.md) |
| Execution roadmap, sprint, backlog | [EXECUTION_BLUEPRINT.md](EXECUTION_BLUEPRINT.md) |
| System architecture and module boundaries | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Data provider policy and freshness | [DATA_SOURCES.md](DATA_SOURCES.md) |
| AI permissions and output boundaries | [AI_BOUNDARIES.md](AI_BOUNDARIES.md) |
| Privacy, secrets, and threat model | [SECURITY.md](SECURITY.md) |
| Trading disclaimer copy and placement | [TRADING_DISCLAIMER.md](TRADING_DISCLAIMER.md) |
| UI rules and visual vocabulary | [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) |
| Engineering workflow | [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) |
| Contribution process | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Long-lived technical decisions | [adr/](adr/) |

## Current Status

Phase V1 planning is frozen. Implementation should start from V1-S1 in [EXECUTION_BLUEPRINT.md](EXECUTION_BLUEPRINT.md).

Do not reopen product scope during implementation unless a blocker appears. Use ADRs for architecture changes and update the canonical file for the affected topic.

## Non-Negotiable Boundaries

- Local-first and single-user.
- Decision-support only.
- No broker login, cookies, order placement, or account integration.
- No predictive AI, AI buy/sell alerts, or public recommendations.
- No realtime or tick-data promise.
- No full news article storage or republication.
- No SaaS, multi-user, auth, billing, or social/copy trading scope.
