# AGENTS.md — SahamLens

SahamLens is a personal trading companion for one retail IDX trader. It is local-first, public-repo-safe, and AI-assisted. AI explains; the user decides. It is **not** a broker, signal service, portfolio manager, or SaaS platform.

> **Phase aktif:**---*
> **Status *planning*:** *frozen*
> **Branch:** `---`
---

## 1. Documentation Map

Always cite or edit the canonical file instead of duplicating facts here.

| Topic | Source of Truth |
|---|---|
| Product scope, goals, non-goals | [.docs/PRD.md](.docs/PRD.md) |
| Execution roadmap, sprint backlog | [.docs/EXECUTION_BLUEPRINT.md](.docs/EXECUTION_BLUEPRINT.md) |
| System architecture, module boundaries | [.docs/ARCHITECTURE.md](.docs/ARCHITECTURE.md) |
| Data providers, freshness, coverage | [.docs/DATA_SOURCES.md](.docs/DATA_SOURCES.md) |
| AI rules, output boundaries, safety | [.docs/AI_BOUNDARIES.md](.docs/AI_BOUNDARIES.md) |
| Privacy, secrets, threat model | [.docs/SECURITY.md](.docs/SECURITY.md) |
| Trading disclaimer copy, placement | [.docs/TRADING_DISCLAIMER.md](.docs/TRADING_DISCLAIMER.md) |
| UI rules, visual vocabulary | [.docs/DESIGN_SYSTEM.md](.docs/DESIGN_SYSTEM.md) |
| Engineering workflow | [.docs/ENGINEERING_STANDARDS.md](.docs/ENGINEERING_STANDARDS.md) |
| Long-lived technical decisions | [.docs/adr/](.docs/adr/) |
| Agent workflow template (this skeleton) | `@C:\Users\transcend\.claude\WORKFLOW.md` |
| RTK shell tooling rules | `@C:\Users\transcend\.codex\RTK.md` |

**Rules:**
- Before claiming a fact, check the relevant source-of-truth doc.
- Before changing a fact, edit the canonical doc.
- Before creating a new doc, check whether it belongs in an existing doc.
- Keep planning history out of active docs unless the owner explicitly asks for an archive.

---

## 2. Progress — Phase Schedule

### 2.1 Roadmap

```
Phase 0: Docs Readiness + Foundation
  → Phase V1-S1: Provider Health + Data Quality
  → Phase V1-S2: Ticker Lifecycle + Fundamental Snapshot
  → Phase V1-S3: Screener
  → Phase V1-S4: Journal Review + Strategy Rules
  → Phase V1-S5: Polish + Runtime Readiness + UX Stabilization
  → Phase V1-S6: Alerts + Telegram Optional + Earnings Summary
  → Release Readiness: PR review, merge, release
```

**Phase V1-S1 — Provider Health + Data Quality**
- Make data trust visible before building dependent features.
- Provider health schema, CLI refresh, Data Quality UI shell.

**Phase V1-S2 — Ticker Lifecycle + Fundamental Snapshot**
- Coverage tiers, lifecycle states, lightweight fundamentals with confidence.
- Coverage classifier, fundamental snapshot ingestion, CLI, UI.

**Phase V1-S3 — Screener**
- Transparent rule evaluation with freshness/confidence gates.
- No signal language, no hidden scoring.

**Phase V1-S4 — Journal Review + Strategy Rules**
- Weekly behavior review from journal entries.
- Simple named strategy-rule checks, no DSL.

**Phase V1-S5 — Polish + Runtime Readiness + UX Stabilization**
- Consistent actionable empty/error/loading states.
- Runtime readiness bootstrap, DuckDB lock hardening.

**Phase V1-S6 — Alerts + Telegram Optional + Earnings Summary**
- Local alert rules/events, acknowledge/dismiss/false-positive lifecycle.
- Optional manual Telegram delivery, manual-first earnings summaries.

---

### 2.2 Reusable Phase Gate

Universal checklist — must pass before any phase is considered exited:

- [x] **Scope:** all deliverables for this phase done; scope creep documented as "carry-forward"
- [x] **Build:** Python + web build zero error; typecheck clean
- [x] **Lint/format:** ruff + prettier pass; no debug artifacts; no `any` without justification
- [x] **Agent handoff:** each implementation agent left a handoff note
- [x] **Tests:** relevant tests pass; regressions documented
- [x] **Docs:** AGENTS.md or CLAUDE.md updated if active phase or stack changed
- [ ] **Critic review:** Devil's Advocate review completed; actionable alternatives documented
- [ ] **Phase log:** new entry written in §2.5 with lesson + carry-forward

---

### 2.3 Active Phase

**Active phase:** V1 — Release Readiness / PR Review

**Sprint focus:** Review codebase, confirm migration safety, verify no signal/profit language, audit Telegram secret boundary, run full verification suite, and prepare merge.

**Orchestrator:** Lead Technical Orchestrator

**Next:** Open PR / review branch, or run owner-approved manual local migration smoke test.

---

### 2.4 Exit Criteria

Phase V1 exits only when:

- [ ] Full Python + web verification suite passes (tests, typecheck, lint, format, build)
- [ ] No signal/profit/prediction language in UI, CLI, or core copy
- [ ] Telegram secrets never rendered or committed
- [ ] Migration safety confirmed — no stale local DB breaks UX without runtime guidance
- [ ] Critic / Devil's Advocate review completed
- [ ] Known gaps documented in handoff
- [ ] Merge ready — open PR or branch ready for owner review

---

### 2.5 Phase Log

| Phase | Status | Lesson | Carry-forward |
|---|---|---|---|
| V1-S0 Docs Readiness | Complete | Pre-commit line-ending hook touched many files during all-files run; restore noise and commit only docs/alignment. | Main is ahead of origin until pushed. |
| V1-S1 Provider Health + DQ | Complete | Direct path pytest on subpackage hit import-root quirk; full repo pytest is the CI-like check. | Watch legacy freshness naming during S2 integration. |
| V1-S2 Ticker + Fundamentals | Complete | DuckDB file locks when multiple CLI commands read/write in parallel. | Run refresh/read commands sequentially. |
| V1-S3 Screener | Complete | Direct path pytest still has package-root quirks; full repo pytest is reliable. | Dogfood pending — owner opt-in. |
| V1-S4 Journal + Strategy | Complete | Stale local DB breaks dependent UI pages; runtime bootstrap command is the fix. | V1-S4 Dogfood pending — owner opt-in. |
| V1-S4.1 Runtime Lock Harden | Complete | Windows cross-process DuckDB contention, not a production leak. | Prefer read-only connections and sequential DB-backed fetches to avoid lock. |
| V1-S5 Polish + Runtime | Complete | Keeping copy calm and actionable without changing core business logic was the main challenge. | No alerts/Telegram/earnings scope was added. |
| V1-S6 Alerts + Telegram + Earnings | Complete | DuckDB FK limitation required updating event status before inserting summary rows. Telegram missing config is not an app failure. | Local DB was not migrated; `scripts.runtime status --json` is read-only. |
| V1-S6 Release Readiness / PR Review | Complete | CRLF warnings are Windows line-ending noise, not diff errors. Manual smoke test remains owner opt-in. | Next: open PR or run owner-approved migration smoke test. |

---

## 3. Stack (Locked)

| Layer | Decision |
|---|---|
| Web | Next.js 15 App Router, TypeScript strict, Tailwind, shadcn/ui |
| Core | Python 3.11+, strict typing |
| Database | DuckDB file-based local database (`data/private/sahamlens.duckdb`) |
| Charts | `lightweight-charts` |
| Tests | `vitest`, `pytest`, `hypothesis` |
| Lint/format | `eslint`, `prettier`, `ruff`, `mypy` |
| Package managers | `pnpm`, `uv` |
| AI | Provider-agnostic wrapper in `packages/core/ai` |
| Agent runtime | Local long-running Hermes process (`services/hermes`), outbound long-polling Telegram; Discord gateway later. See ADR-0019. |

Stack changes require an explicit ADR or user approval.

**Allowed by ADR-0019 (previously deferred):**
- Long-running service — **only** the local Hermes runtime (single-user, single-process, outbound long-polling, no inbound port). Not a license for other services.

**Deferred (still out of scope):**
- FastAPI sidecar, generic background scheduler, inbound HTTP server/webhook, multi-process orchestration
- Real-time or intraday alerting
- Broker integration, account sync, order placement
- Push notification beyond Telegram/Discord agentic surface
- Cloud sync, multi-user auth, SaaS, billing

**Banned unless explicitly overridden:**
- Strategy DSL, custom scripting, buy/sell/hold signal language
- Predictive AI price forecasts
- Automated IDX scraping/crawling
- Any dependency that requires paid API keys by default

---

## 4. AI Instructions

### 4.1 Before Coding

1. Read this file first, then the relevant documents from §1.
2. Check active phase in §2.3 before starting any work.
3. Run `rtk git status --short --branch`. If WIP overlaps relevant area, tell the orchestrator before editing.
4. Confirm whether code scaffolding is actually requested. If user asks only for docs/strategy, do not scaffold.
5. Check file tree before creating new files or folders.

### 4.2 Code Rules (Non-Negotiable)

- Keep business logic in `packages/core`.
- Keep `scripts` as orchestration only.
- Keep `apps/web` presentation-focused.
- `packages/core/*` must not import `apps/web/**` or `scripts/**`.
- Use strict TypeScript and strict Python typing.
- Avoid `any` and `# type: ignore` unless a short why is included.
- Add tests for changed behavior.
- Do not commit private data from `data/private/*`.
- Prefer small vertical PRs.
- Use conventional commits.

### 4.3 Anti-Slop

- Do not claim something is complete before checking the actual file or running verification.
- Do not add new architectural layers or parallel systems without orchestrator approval.
- Do not mark a feature complete without validation evidence.
- Do not introduce new dependencies unless the orchestrator approves.
- Do not duplicate evaluator/classifier logic in React or CLI — core owns domain rules.

### 4.4 Scope Discipline

Build vertically, not horizontally. One polished slice beats several half-finished ones.

Build order for this project:
1. Data trust (Provider Health, Data Quality)
2. Data coverage (Ticker Lifecycle, Fundamentals)
3. Screening (Screener)
4. Behavior review (Journal, Strategy Rules)
5. Polish gate (Runtime Readiness, UX)
6. Alert/Earnings lifecycle

When in doubt between spectacle and correctness, prioritize correctness.

### 4.5 Communication

- Use concise Indonesian by default when the user writes in Indonesian.
- Refer to exact files and rules when explaining decisions.
- When uncertain, present 2-3 concrete options with trade-offs instead of improvising.
- Flag conflicts early: locked stack changes, phase jumps, scope creep, direction regressions.
- During debugging: state what is happening, what was expected, and what evidence supports the conclusion.
- Cite files with paths. If data is insufficient, say so.

### 4.6 Contribution Identity

> **Copy this section verbatim into every project AGENTS.md / CLAUDE.md. Do not modify.**

AI is a ghostwriter. Repository accountability remains with the human owner.

- Do not add `Co-Authored-By: Claude` or any AI/model co-author trailer to commits.
- Do not add "Generated with Claude Code" or equivalent tags to commit messages or PR bodies.
- Do not push commits with AI or bot author identity.
- Do not make AI appear in the GitHub contributor graph.
- Author and committer identity must be the repo owner's human identity configured for the project.
- If AI assistance needs to be disclosed, mention it only in normal prose in a PR description or changelog, never in git metadata.

---

## 5. Implementation Agent Team

| # | Agent Role | Responsibility | Owns | Must Not Do | Handoff Output |
|---|---|---|---|---|---|
| 1 | **Lead Technical Orchestrator** | Sequencing, scope control, task distribution, merge readiness, final validation | Breaking roadmap into tracks; assigning agents; preventing duplication and architecture drift | Skip final validation; assign ambiguous work without acceptance criteria; overload tracks | Phase gate status, next-track assignment, risk summary |
| 2 | **Product / Workflow Architect** | Product flow, user journey, page hierarchy, workflow coherence | Ensuring features support core user workflow — not isolated UI additions | Design features that bypass the core workflow; add pages without user-journey justification | Updated workflow blueprint, journey impact notes |
| 3 | **Frontend Engineer** | UI implementation, page layout, interaction states, accessibility, client-side behavior | Templates, components, navigation, responsive states | Add noisy UI outside the design system; introduce a frontend build step | Files changed, new/interaction states rendered, a11y notes |
| 4 | **Backend Engineer** | API routes, services, storage logic, validation, integration boundaries | Route handlers, service layer, CLI commands, provider integration | Put business logic in route/controller layers; bypass service layer | New/edited routes and services, contract changes, validation rules |
| 5 | **Data / Storage Engineer** | Schema, migrations, persistence rules, seed data, backward compatibility | Database schema files, migration scripts, data access patterns | Introduce schema churn without orchestrator approval; break backward compatibility without ADR | Migration diff, schema diff, compatibility notes |
| 6 | **QA / Validation Engineer** | Test plan, regression checks, acceptance criteria, final validation | Test suite, validation runs, edge-case coverage, regression list | Validate only unit-level assumptions; skip user-facing workflow paths | Test results, regression list, acceptance pass/fail, known gaps |
| 7 | **Security / Safety Engineer** | Input validation, file handling risks, secret handling, path traversal, dependency risk | Security review of all I/O surfaces, credential handling, dependency audit | Introduce unsafe file/subprocess patterns; store secrets in config/logs/render | Security review notes, filed risks, surfaces reviewed |
| 8 | **Performance / Reliability Engineer** | Slow paths, job handling, long-running operations, resource limits, failure recovery | Performance budget, concurrency handling, error recovery paths, blocking UX | Ship code that blocks main thread or UI for >1 s; hide errors with silent retries | Perf benchmarks, bottleneck list, failure-path coverage |
| 9 | **Documentation / Handoff Writer** | Changelog notes, sprint summaries, ADR drafting, agent handoff clarity | Sprint reports, handoff documents, README updates, ADR drafts | Duplicate info already in source-of-truth docs; write verbose non-operational docs | Handoff notes for each completed track, changelog draft |
| 10 | **Critic / Devil's Advocate** | Challenge assumptions, detect overengineering, UX friction, hidden bugs | Pre-release review, alternative proposal generation, scope-creep detection | Block progress without giving actionable alternatives; file complaints without evidence | Review findings, alternative proposals, risk flags |
| 11 | **Release Captain** | Final gate checklist, merge readiness, release notes, done/not-done status | Gate D sign-off, release notes, status summary, known-gap documentation | Mark "done" without validation evidence; merge incomplete work into release branch | Release checklist status, merge readiness verdict, known gaps doc |

**Rule:** No implementation agent may override the Lead Technical Orchestrator's scope without explicitly documenting the reason, risk, and proposed alternative.

---

## 6. Implementation Tracks

| Track | Name | Owner Agent | Purpose | Entry Criteria | Exit Criteria |
|---|---|---|---|---|---|
| T0 | Documentation & Source of Truth | Documentation / Handoff Writer | Keep AGENTS.md, roadmap, architecture, sprint notes aligned | Sprint started; new phase scope defined | All source-of-truth docs updated; ADRs current; handoff notes complete |
| T1 | Product Workflow & UX | Product / Workflow Architect | Ensure app workflow is coherent from entry → main action → completion | Phase scope defines new flow or modifies existing one | Workflow blueprint updated; no orphan pages/states |
| T2 | Frontend Implementation | Frontend Engineer | Implement layouts, components, states, navigation | T1 defines UI to build; design tokens exist | Pages render correctly at 390px+; keyboard navigable; states handled |
| T3 | Backend / CLI Implementation | Backend Engineer | Implement CLI commands, validation, integration | Route contracts defined; storage layer exists | Commands respond correctly; edge cases handled; integration test passes |
| T4 | Data, Storage & Migration | Data / Storage Engineer | Maintain schema safety, migrations, persistence | Schema change or migration required by feature | Migration forward tested; existing data preserved; no silent data loss |
| T5 | AI Provider / Agent Integration | Backend Engineer | Implement provider boundaries, model config, retries | New provider or model config required by feature | Provider integration tested; retry/fallback works; secret handling confirmed |
| T6 | QA, Testing & Regression | QA / Validation Engineer | Validate workflows, regression coverage, edge cases | Feature implementation complete; test plan written | Full test suite passes; regressions documented; acceptance verified |
| T7 | Security & Reliability | Security / Safety Engineer | Review secrets, permissions, unsafe inputs, failure recovery | Feature touches I/O, secrets, file system, subprocess, or network | Security review done; sensitive surfaces enumerated; risks documented |
| T8 | Performance & Runtime Readiness | Performance / Reliability Engineer | Identify bottlenecks, blocking states, runtime constraints | Feature complete; integration test passing | Perf budget met; no blocking UX; job recovery tested |
| T9 | Release & Final Gate | Release Captain | Confirm final state, summarize changes, mark ready/not-ready | All tracks complete; T6/T7/T8 passed | Release checklist signed; known gaps documented; next-step clear |

---

## 7. Orchestrator Operating Model

1. **Read** the Documentation Map (§1) and understand which docs govern the current phase.
2. **Identify** the current sprint/phase from Progress → Phase Schedule (§2).
3. **Confirm** Stack Locked constraints (§3) — no new dependencies or architecture shifts without approval.
4. **Split** the task into implementation tracks (§6). Assign each track an owner agent.
5. **Define** acceptance criteria for each track before implementation starts. State non-goals explicitly.
6. **Assign** each track to the correct owner. Provide track scope, acceptance criteria, non-goals, and handoff format.
7. **Require** each agent to produce a handoff note (§8) at the end of their work.
8. **Run** Critic / Devil's Advocate review (§5 agent #10) before final gate.
9. **Run** QA + Security + Release validation (T6 + T7 + T9) before merging.
10. **Produce** final status for each track: Done, Partial, Blocked, Deferred, or Risk Accepted.

**Operating rule:** Optimize for sequence, coherence, and risk reduction — not maximum parallel work.

---

## 8. Agent Handoff Protocol

Every implementation agent must produce a handoff note at the end of their work. Use this format:

```
## Handoff: [Agent Role]

**Agent:** [Role name]
**Track:** [T0-T9]
**Scope:** [What this agent was asked to do]
**Files/Areas Touched:** [List of files created or modified]
**What Changed:** [Summary of changes]
**What Was Intentionally Not Changed:** [Scope boundaries respected]
**Validation Performed:** [Tests run, manual checks, evidence]
**Known Risks:** [Anything incomplete, fragile, or uncertain]
**Recommended Next Agent:** [Which agent should continue]
**Next Step:** [The single next action the next agent should take]
```

**Rule:** Every handoff must leave enough context for the next agent to continue without re-auditing the entire repository.

---

## 9. Review Gates

| Gate | Stage | Checks | When to Use | Skippable? |
|---|---|---|---|---|
| **A — Scope Confirmation** | Before work starts | Task aligned with current sprint? Owner agent clear? Non-goals stated? Acceptance criteria defined? | Every new task | No |
| **B — Implementation Readiness** | Before coding | Affected files/areas known? Stack constraints respected? Design matches existing patterns? | Every implementation track | No for T2-T5; yes for T0/T9 |
| **C — Validation** | After implementation | Tests or manual checks documented? Regressions considered? Edge cases listed? Handoff note written? | Every track that produced code or schema | No for T2-T8; yes for T0 |
| **D — Release Readiness** | Before merge/ship | Work actually complete? Known gaps documented? Next step clear? Critic review done? Checklist signed? | Every phase/sprint exit | No |

**Gate-skip rule:** Use fewer gates for small changes (single file, <50 lines, no schema change), but never skip Gate C (validation).

---

## 10. Decision Rules

| Priority | Rule |
|---|---|
| 1 | Prefer **existing architecture** over new patterns. Do not invent a new pattern when an existing one works. |
| 2 | Prefer **small, sequenced changes** over broad rewrites. One file changed correctly beats ten files changed incompletely. |
| 3 | Prefer **user workflow completion** over isolated technical polish. A working end-to-end flow is worth more than a perfectly refactored component with no user path. |
| 4 | Prefer **explicit ownership** over anonymous "agent" work. Every task has a named owner. |
| 5 | Do **not introduce new dependencies** unless the orchestrator approves. A new import is an architecture decision. |
| 6 | Do **not mark a feature complete** without validation evidence. "It compiles" is not validation. |
| 7 | Do **not modify roadmap, architecture, or stack constraints silently**. Propose changes in a handoff note or ADR draft. |
| 8 | **When in doubt, document the uncertainty** and propose the smallest safe next step. A documented question is better than an undocumented assumption. |

---

## 11. Recommended Workflow Optimizations

1. **RACI-style clarity** — R: implementation owner, A: Lead Orchestrator, C: Critic/Security/QA, I: Documentation/Release Captain.
2. **Separate builder and reviewer roles** — Same agent should not be sole reviewer of its own work.
3. **Keep Progress → Phase Schedule as execution truth** — Roadmap (§2.1) says what *should* happen; schedule (§2.3) says what *is* being executed.
4. **Add "Non-Goals" per sprint** — Prevents scope creep and random refactors.
5. **Add "Definition of Done" per track** — Done = implemented + validated + documented + handed off.
6. **Add "Risk Register" per sprint** — Keep small (5-10 risks max), update as risks close or emerge.
7. **"Next Agent Recommendation" is mandatory** — Every handoff must suggest which agent should continue next.

---

## 12. Final Notes for Future Agents

1. **This file is the operating system of the project.** Read it before any code change.
2. **The orchestrator is your entry point.** If scope is unclear, ask. Do not improvise scope.
3. **You are a specialist, not a generalist.** Flag cross-boundary issues in your handoff — do not fix them yourself unless the orchestrator says so.
4. **Handoff is not optional.** If your track ends without a handoff note (§8), the work is incomplete.
5. **Validation is not optional.** If your track ends without evidence that it works, the work is incomplete.
6. **Scope is the enemy of quality.** Flag oversized scope to the orchestrator immediately.
7. **Read the docs before the code.** If a doc contradicts the code, flag the contradiction.
8. **Critic is your friend.** Welcome the review. Engage with alternatives.
9. **One PR = one concern.** Do not bundle refactors with features. Split concerns or document why they must be bundled.
10. **Git history is the permanent record.** Write clear conventional commits. Do not force-push shared branches.

---

## Scope Guardrails

**Allowed V1 work:**
- Data Quality Dashboard
- Provider Health
- Ticker lifecycle and coverage
- Fundamental Snapshot with completeness/confidence
- Screener with transparent no-signal language
- Local alert rules/events with false-positive feedback
- Weekly Journal Review
- Simple Strategy Rules
- Earnings Summary manual-first

**Out of scope for V1:**
- Broker login, cookies, sessions, account sync, or order placement
- Realtime or tick-data promise
- Predictive AI, AI buy/sell alerts, or forecasting alerts
- Public recommendations, signal selling, SaaS, auth, billing, or multi-user scope
- Automated IDX crawling
- Full news article storage or republication
- Strategy DSL

---

## Repo Mental Model

```
apps/web/          Next.js dashboard
packages/core/     Python data core
  data_sources     providers and source metadata
  data_quality     provider health, freshness, coverage
  fundamentals     snapshots, completeness, confidence
  screener         transparent rules and results
  alerts           local rules, events, feedback
  earnings         manual-first earnings metadata
  journal          entries and weekly review
  strategy         simple rules, no DSL
  runtime          readiness, schema status, bootstrap contract
  ai               LLM wrapper and validation
  schemas          Pydantic models and migrations
scripts/           CLI orchestration
data/sample/       fake committed data
data/private/      ignored real local data
prompts/system/    versioned prompt templates
config/            example config committed, local config ignored
.docs/             canonical documentation
```

---

*This AGENTS.md follows the global WORKFLOW.md template at `@C:\Users\transcend\.claude\WORKFLOW.md`. Changes to the template structure should be made there and propagated here.*
