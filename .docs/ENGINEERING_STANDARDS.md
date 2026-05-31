# Engineering Standards

## Baseline

SahamLens is a small local-first project. Prefer boring, typed, testable code over broad abstractions.

## Tooling

- TypeScript strict for `apps/web`.
- Python 3.11+ with strict typing for `packages/core`.
- pnpm for web workspace.
- uv for Python workspace.
- eslint and prettier for TypeScript.
- ruff and mypy for Python.
- vitest for TypeScript tests.
- pytest and hypothesis for Python tests.

## Code Rules

- Keep business logic in `packages/core`.
- Keep scripts as orchestration only.
- Keep UI logic presentation-focused.
- Do not import `apps/web` from `packages/core`.
- Do not import `scripts` from `packages/core`.
- Add comments only for non-obvious why.
- Extract abstraction after real duplication, not anticipation.
- Avoid `any` and `# type: ignore` unless a short why is included.

## Test Rules

Expected gates:

- Financial calculations: at least 90 percent coverage.
- Other core modules: at least 70 percent coverage.
- Schema changes: schema/repository tests.
- CLI changes: smoke tests.
- UI changes: component or route-level tests where practical.
- Data-quality behavior: tests for fresh, stale, failed, partial, and unknown.
- Alerts: tests for lifecycle and false-positive feedback.

Do not claim work is complete before relevant checks pass or a limitation is explicitly reported.

## Dependency Rules

Before adding a dependency, answer:

1. What concrete feature needs it?
2. Can this be done in less than 50 lines without it?
3. What is the install, bundle, security, or maintenance cost?

Architecture-changing dependencies require ADR.

## Git and PR Rules

- Use conventional commits.
- Keep PRs small and reviewable.
- Prefer vertical slices over broad horizontal rewrites.
- Do not include AI co-author trailers or generated-with metadata.
- Do not commit private data.
- Squash merge to `main` unless owner decides otherwise.

Suggested branch prefix:

- `v1/provider-health-*`
- `v1/fundamentals-*`
- `v1/screener-*`
- `v1/journal-*`
- `v1/alerts-*`

## Documentation Rules

- Update the canonical doc for the topic.
- Do not duplicate long decisions across docs.
- Add ADR only for durable architecture decisions.
- Keep historical planning out of active execution docs.
