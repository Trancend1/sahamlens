# ADR-0015: Simple Strategy Rules and No DSL

Status: Accepted
Date: 2026-06-02

## Context

V1-S4 adds Weekly Journal Review and Strategy Rules. These features help the owner
review behavior and plan discipline from local journal entries. Without a boundary,
strategy rules can drift into a configurable strategy language, backtesting surface,
optimization engine, or trading signal product.

## Decision

V1 strategy rules are simple named checks. SahamLens must not introduce a strategy
DSL in V1.

Allowed rule behavior:

- Named rule definitions.
- Explicit required journal fields.
- Pass, fail, needs data, or skipped evaluation status.
- Evidence from journal entries.
- Violation reasons.
- Caveats when data is incomplete.
- Date-range evaluation.
- Weekly review summaries for behavior reflection.

Rejected rule behavior:

- Custom scripting or expression language.
- User-authored DSL.
- Strategy optimization.
- Backtesting or performance ranking.
- Predictive scoring.
- Buy, sell, hold, strong buy, safe, guaranteed, or equivalent signal language.
- Broker/order integration.

## Rule Semantics

Each V1 strategy rule must declare:

- Rule identifier.
- Name.
- Description.
- Rule category.
- Required fields.
- Evaluation status vocabulary.
- Violation reason vocabulary.
- Caveat behavior.
- Created and updated timestamps.

Rules must remain inspectable and auditable. If a journal entry lacks required data,
the rule should return `needs_data` instead of pretending confidence.

## Weekly Review Semantics

Weekly Journal Review is behavior review, not a performance terminal.

The review may summarize:

- Number of plans reviewed.
- Rule pass/fail/needs-data counts.
- Repeated missing fields.
- Repeated violations.
- Evidence snippets from journal entries.
- Caveats and follow-up prompts for the owner.

The review must not claim profitability, skill, prediction, or trade approval.

## Schema Implications

Schema should support:

- Weekly review run metadata.
- Weekly review findings.
- Strategy rule definitions.
- Strategy rule evaluations.
- Strategy rule violation details.
- Evidence and caveat storage.
- Date ranges and timestamps.

The schema should stay narrow enough for local DuckDB and single-user use.

## AI Boundary

AI may explain journal evidence and caveats. AI must not approve a trade plan,
recommend a ticker, predict outcomes, or turn rule failures into public signals.

## Consequences

Positive:

- Keeps V1 focused on behavior reflection.
- Avoids brittle DSL parsing and strategy-engine scope.
- Makes rule output auditable and testable.
- Reduces false confidence from incomplete journal entries.

Trade-offs:

- V1 cannot express arbitrary strategies.
- Rules may feel rigid until dogfooding identifies the most useful named checks.
- Advanced analytics remain deferred.

## Follow-Up

V1-S4 schema, core logic, CLI, and UI must consume this ADR. Any future custom
strategy language requires a new ADR after V1.
