# Contributing

SahamLens is a personal local-first project. Contributions should protect that scope.

## Before You Start

1. Read [README.md](README.md).
2. Check the source-of-truth map.
3. Confirm the task fits the active V1 roadmap in [EXECUTION_BLUEPRINT.md](EXECUTION_BLUEPRINT.md).
4. If the task changes architecture, data trust, AI safety, or scope, propose an ADR first.

## Accepted Contributions

- V1 backlog tickets.
- Tests and small refactors that reduce risk.
- Documentation cleanup in canonical files.
- Data quality, freshness, coverage, confidence, screener, alert, journal, and earnings work within V1 scope.

## Not Accepted Without New ADR/Phase Unlock

- Broker integration.
- Realtime market data infrastructure.
- Predictive AI or buy/sell signals.
- SaaS, auth, billing, teams, or multi-user features.
- Strategy DSL.
- Social sentiment ingestion.
- Full news article storage.

## PR Checklist

- Scope matches a ticket or approved fix.
- Tests relevant to changed files pass.
- Docs updated only where canonical.
- No `data/private/*` content.
- No secrets.
- No AI co-author metadata.
- User-facing AI copy follows [AI_BOUNDARIES.md](AI_BOUNDARIES.md).

## Commit Style

Use conventional commits:

- `docs: simplify v1 execution docs`
- `feat: add provider health model`
- `test: cover freshness states`
- `fix: handle stale ticker coverage`

Do not add:

- `Co-Authored-By: Codex`
- generated-by trailers
- bot author metadata
