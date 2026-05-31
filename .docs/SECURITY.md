# Security and Privacy

## Security Model

SahamLens is local-first and single-user. The primary security goal is to keep private trading data, credentials, journals, portfolio files, and local database contents out of the public repository and out of unnecessary external services.

## Data Locations

| Path | Policy |
|---|---|
| `data/private/` | Real local data. Must stay gitignored. |
| `data/sample/` | Fake committed data only. |
| `config/*.yml` | Local config. Must stay gitignored. |
| `config/*.example.yml` | Safe examples only. |
| `.docs/` | Public-safe documentation only. |

## Secrets

Never commit:

- API keys.
- Broker credentials.
- Cookies or sessions.
- Portfolio exports with real holdings.
- Journal entries with private trade details.
- Local DuckDB files.
- Raw LLM logs that include private data.

## Broker Boundary

V1 has no broker integration. The app must not:

- Store broker credentials.
- Reuse broker cookies or sessions.
- Scrape authenticated broker pages.
- Place, stage, or submit orders.
- Sync account balances or holdings through broker login.

Manual CSV import/export may exist only as local user-controlled files.

## LLM Privacy

Before sending context to an LLM:

- Include only the minimum required fields.
- Redact private identifiers where practical.
- Do not send raw portfolio files or complete journal history by default.
- Preserve source timestamps and caveats.

The user must be able to understand what data is used in an AI summary.

## Public Repository Safety

Required controls:

- `data/private/*` remains ignored.
- Secret scanning stays enabled.
- Sample data is fake.
- Docs avoid private account details.
- Commits do not include AI co-author metadata unless explicitly required by the owner.

## Dependency Policy

New dependencies require:

1. Concrete feature need.
2. Check whether the feature is practical in less than 50 lines without dependency.
3. Review install, maintenance, security, and bundle/runtime impact.
4. ADR if the dependency changes architecture or trusted boundaries.

## Incident Response

If private data is committed:

1. Stop work.
2. Identify affected files and commits.
3. Remove from working tree.
4. Rotate exposed credentials if any.
5. Rewrite history only with explicit owner approval.
6. Document the incident in a private-safe way.
