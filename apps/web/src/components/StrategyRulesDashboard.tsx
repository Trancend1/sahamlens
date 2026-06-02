import Link from "next/link";
import type { StrategyRule, StrategyRuleEvaluation } from "@/lib/strategyRules";

const STATUS_COPY: Record<string, { label: string; className: string }> = {
  pass: { label: "Pass", className: "border-emerald-500/40 text-emerald-300" },
  fail: { label: "Fail", className: "border-red-500/40 text-red-300" },
  needs_data: { label: "Needs Data", className: "border-amber-500/40 text-amber-300" },
  skipped: { label: "Skipped", className: "border-muted/40 text-muted" },
};

interface Props {
  rules: StrategyRule[];
  evaluations: StrategyRuleEvaluation[];
  error: string | null;
}

export function StrategyRulesDashboard({
  rules,
  evaluations,
  error,
}: Props): React.ReactElement {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">
          <Link href="/" className="hover:text-fg">
            SahamLens
          </Link>{" "}
          / V1-S4
        </p>
        <h1 className="mt-1 text-3xl font-semibold">Strategy Rules</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Simple named checks for journal hygiene. No custom DSL, no optimization, and not trade
          signals.
        </p>
      </header>

      {error ? <ErrorPanel error={error} /> : null}
      {!error && rules.length === 0 && evaluations.length === 0 ? <EmptyState /> : null}
      {!error && (rules.length > 0 || evaluations.length > 0) ? (
        <>
          <Summary evaluations={evaluations} />
          <RuleList rules={rules} />
          <EvaluationList evaluations={evaluations} />
        </>
      ) : null}
    </main>
  );
}

function Summary({ evaluations }: { evaluations: StrategyRuleEvaluation[] }): React.ReactElement {
  const pass = evaluations.filter((item) => item.evaluation_status === "pass").length;
  const fail = evaluations.filter((item) => item.evaluation_status === "fail").length;
  const needsData = evaluations.filter((item) => item.evaluation_status === "needs_data").length;
  const skipped = evaluations.filter((item) => item.evaluation_status === "skipped").length;
  const items = [
    ["Pass", pass],
    ["Fail", fail],
    ["Needs Data", needsData],
    ["Skipped", skipped],
  ] as const;
  return (
    <section className="grid gap-3 sm:grid-cols-4">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-md border border-muted/30 bg-white/[0.02] p-4">
          <p className="text-xs uppercase tracking-widest text-muted">{label}</p>
          <p className="mt-2 text-2xl font-semibold">{value}</p>
        </div>
      ))}
    </section>
  );
}

function RuleList({ rules }: { rules: StrategyRule[] }): React.ReactElement {
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <h2 className="text-sm font-medium">Named Rules</h2>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {rules.map((rule) => (
          <article key={rule.rule_id} className="rounded border border-muted/20 p-4">
            <p className="font-medium">{rule.name}</p>
            <p className="mt-1 text-xs uppercase tracking-widest text-muted">
              {rule.rule_category} / {rule.violation_code}
            </p>
            <p className="mt-2 text-sm text-muted">{rule.description}</p>
            <p className="mt-2 text-xs text-muted">
              Required fields: {rule.required_fields.length ? rule.required_fields.join(", ") : "none"}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}

function EvaluationList({
  evaluations,
}: {
  evaluations: StrategyRuleEvaluation[];
}): React.ReactElement {
  return (
    <section className="grid gap-3">
      <h2 className="text-sm font-medium">Evaluation Results</h2>
      {evaluations.length === 0 ? (
        <p className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm text-muted">
          Belum ada evaluation results. Generate weekly review or run rules evaluate first.
        </p>
      ) : (
        evaluations.map((evaluation) => {
          const status = STATUS_COPY[evaluation.evaluation_status];
          return (
            <article key={evaluation.evaluation_id} className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-mono text-sm">{evaluation.rule_id}</p>
                  <p className="mt-1 text-xs text-muted">
                    {evaluation.symbol ?? "n/a"} / journal {evaluation.journal_id ?? "n/a"}
                  </p>
                </div>
                <span className={`rounded border px-2 py-1 text-xs uppercase tracking-widest ${status.className}`}>
                  {status.label}
                </span>
              </div>
              <p className="mt-3 text-sm text-fg">{evaluation.reason}</p>
              <ViolationList evaluation={evaluation} />
              <List title="Evidence" items={evaluation.evidence} />
              <List title="Caveats" items={evaluation.caveats} />
            </article>
          );
        })
      )}
    </section>
  );
}

function ViolationList({ evaluation }: { evaluation: StrategyRuleEvaluation }): React.ReactElement | null {
  if (evaluation.violations.length === 0) return null;
  return (
    <div className="mt-3">
      <p className="text-xs uppercase tracking-widest text-muted">Violation reasons</p>
      <ul className="mt-2 list-inside list-disc text-sm text-muted">
        {evaluation.violations.map((violation) => (
          <li key={violation.violation_id}>
            {violation.violation_code}: {violation.violation_detail}
          </li>
        ))}
      </ul>
    </div>
  );
}

function EmptyState(): React.ReactElement {
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm">
      <p className="font-medium">Belum ada strategy-rule data.</p>
      <p className="mt-2 text-muted">
        Run{" "}
        <code className="font-mono">
          uv run python -m scripts.journal_review --json rules evaluate --start 2026-05-25 --end
          2026-06-01
        </code>{" "}
        after journal entries are ready.
      </p>
    </section>
  );
}

function ErrorPanel({ error }: { error: string }): React.ReactElement {
  return (
    <section className="rounded-md border border-red-500/40 bg-red-500/[0.05] p-5 text-sm">
      <p className="font-medium text-red-300">Gagal membaca strategy rules.</p>
      <pre className="mt-3 whitespace-pre-wrap text-xs text-red-200">{error}</pre>
    </section>
  );
}

function List({ title, items }: { title: string; items: string[] }): React.ReactElement | null {
  if (items.length === 0) return null;
  return (
    <div className="mt-3">
      <p className="text-xs uppercase tracking-widest text-muted">{title}</p>
      <ul className="mt-2 list-inside list-disc text-sm text-muted">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
