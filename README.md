# SahamLens

Personal trading companion untuk satu trader retail IDX. Local-first, public-repo-safe, AI-assisted. AI explains; the user decides.

SahamLens is not SaaS, not a signal seller, not an autonomous trader, and not broker integration.

Status: Sprint 5 — Documentation & Verification. All core V1 data operations available from WebUI.

Personal learning and analysis tool only. Not financial advice. Read [DISCLAIMER.md](DISCLAIMER.md) before use.

## Quick Start

### Prerequisites

| Tool | Minimum | Check |
|---|---|---|
| Node.js | 22.13.0 | `node --version` |
| pnpm | 11.1.2 recommended | `pnpm --version` |
| Python | 3.11+ | `python --version` |
| uv | 0.11+ recommended | `uv --version` |
| git | 2.40+ | `git --version` |
| pre-commit | 4.x | `pre-commit --version` |

Use `corepack enable` if pnpm is not available.

### Quick Start

```bash
git clone <repo-url> sahamlens
cd sahamlens

cp .env.example .env.local

uv sync
pnpm install

pnpm dev
```

The web app runs at `http://localhost:3000`.

On first run, the application automatically runs migration + bootstrap.
No manual CLI steps needed to get started.

### Post-Setup

1. Add watchlist symbols or import portfolio from the WebUI
2. Go to the **Operations** dashboard at `/operations`
3. Click **Refresh All** to populate initial data
4. Refresh individual sections (Prices, Fundamentals, News, Screener) on demand

### Windows Notes

If the web app cannot find the project Python, start dev with:

```powershell
$env:PYTHON_BIN=(Resolve-Path ".venv/Scripts/python.exe").Path
pnpm.cmd --filter @sahamlens/web dev
```

### CLI Reference

Most operations are available from the WebUI Operations dashboard. CLI commands
(`uv run python -m scripts.*`) remain available for advanced/programmatic use,
schedule integration, and troubleshooting.

### Verification

```bash
pnpm --filter @sahamlens/web lint
pnpm --filter @sahamlens/web typecheck
pnpm --filter @sahamlens/web test
pnpm --filter @sahamlens/web build

uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest -q
```

## Repo Layout

```text
apps/web/          Next.js dashboard
packages/core/     Python data core
scripts/           CLI orchestration
data/sample/       fake committed data
data/private/      ignored real local data
prompts/system/    prompt templates
config/            example config committed, local config ignored
.docs/             canonical documentation
```

## Documentation

- Agent orientation: [AGENTS.md](AGENTS.md)
- Documentation map: [.docs/README.md](.docs/README.md)
- Product scope: [.docs/PRD.md](.docs/PRD.md)
- Execution plan: [.docs/EXECUTION_BLUEPRINT.md](.docs/EXECUTION_BLUEPRINT.md)
- Architecture: [.docs/ARCHITECTURE.md](.docs/ARCHITECTURE.md)
- Data sources: [.docs/DATA_SOURCES.md](.docs/DATA_SOURCES.md)
- ADRs: [.docs/adr/](.docs/adr/)

## Scope Guardrails

Allowed: local decision support, data quality, provider health, fundamentals, screener, alerts, journal review, simple strategy rules, and manual-first earnings summary.

Rejected for V1: broker integration, realtime/tick-data promise, predictive AI, buy/sell alerts, public recommendations, SaaS/multi-user scope, automated IDX crawling, full article storage, and strategy DSL.

## License

Code is MIT licensed unless a file states otherwise. Private local data is not part of this repository and remains owned by the user.

## Disclaimer

See [DISCLAIMER.md](DISCLAIMER.md) and [.docs/TRADING_DISCLAIMER.md](.docs/TRADING_DISCLAIMER.md).

SahamLens explains available evidence and caveats. It does not provide financial advice, recommend trades, or execute orders.
