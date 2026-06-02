import Link from "next/link";
import type {
  CompletenessState,
  ConfidenceLevel,
  CoverageTier,
  FreshnessState,
  LifecycleStatus,
  ScreenerRun,
} from "@/lib/screener";

const COVERAGE_COPY: Record<CoverageTier, { label: string; className: string }> = {
  tier_a: { label: "Tier A", className: "border-emerald-500/40 text-emerald-300" },
  tier_b: { label: "Tier B", className: "border-amber-500/40 text-amber-300" },
  tier_c: { label: "Tier C", className: "border-red-500/40 text-red-300" },
};

const LIFECYCLE_COPY: Record<LifecycleStatus, { label: string; className: string }> = {
  active: { label: "Active", className: "border-emerald-500/40 text-emerald-300" },
  suspended: { label: "Suspended", className: "border-amber-500/40 text-amber-300" },
  delisted: { label: "Delisted", className: "border-red-500/40 text-red-300" },
  renamed: { label: "Renamed", className: "border-sky-500/40 text-sky-300" },
  unknown: { label: "Unknown", className: "border-muted/40 text-muted" },
};

const FRESHNESS_COPY: Record<FreshnessState, { label: string; className: string }> = {
  fresh: { label: "Fresh", className: "border-emerald-500/40 text-emerald-300" },
  delayed: { label: "Delayed", className: "border-sky-500/40 text-sky-300" },
  stale: { label: "Stale", className: "border-amber-500/40 text-amber-300" },
  failed: { label: "Failed", className: "border-red-500/40 text-red-300" },
  partial: { label: "Partial", className: "border-yellow-500/40 text-yellow-200" },
  unknown: { label: "Unknown", className: "border-muted/40 text-muted" },
};

const COMPLETENESS_COPY: Record<CompletenessState, { label: string; className: string }> = {
  complete: { label: "Complete", className: "border-emerald-500/40 text-emerald-300" },
  partial: { label: "Partial", className: "border-amber-500/40 text-amber-300" },
  sparse: { label: "Sparse", className: "border-yellow-500/40 text-yellow-200" },
  missing: { label: "Missing", className: "border-red-500/40 text-red-300" },
};

const CONFIDENCE_COPY: Record<ConfidenceLevel, { label: string; className: string }> = {
  high: { label: "High", className: "border-emerald-500/40 text-emerald-300" },
  medium: { label: "Medium", className: "border-amber-500/40 text-amber-300" },
  low: { label: "Low", className: "border-yellow-500/40 text-yellow-200" },
  none: { label: "None", className: "border-red-500/40 text-red-300" },
};

interface Props {
  run: ScreenerRun | null;
  error: string | null;
}

export function ScreenerDashboard({ run, error }: Props): React.ReactElement {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">
          <Link href="/" className="hover:text-fg">
            SahamLens
          </Link>{" "}
          / V1-S3
        </p>
        <h1 className="mt-1 text-3xl font-semibold">Screener</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Transparent local filters that show matched rows, exclusions, missing fields, freshness,
          and confidence caveats.
        </p>
      </header>

      {error ? <ErrorPanel error={error} /> : null}
      {run ? (
        <>
          <RuleSummary run={run} />
          {run.results.length === 0 ? <EmptyState /> : <ResultTable run={run} />}
        </>
      ) : null}
    </main>
  );
}

function RuleSummary({ run }: { run: ScreenerRun }): React.ReactElement {
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-muted">Rule</p>
          <h2 className="mt-1 text-xl font-semibold">{run.rule.name}</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted">{run.rule.description}</p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-center text-sm">
          <Metric label="Universe" value={run.universe_count} />
          <Metric label="Included" value={run.included_count} />
          <Metric label="Excluded" value={run.excluded_count} />
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Badge label={`Min ${COVERAGE_COPY[run.rule.min_coverage_tier].label}`} className={COVERAGE_COPY[run.rule.min_coverage_tier].className} />
        {run.rule.min_fundamental_completeness ? (
          <Badge
            label={`Completeness ${COMPLETENESS_COPY[run.rule.min_fundamental_completeness].label}`}
            className={COMPLETENESS_COPY[run.rule.min_fundamental_completeness].className}
          />
        ) : null}
        {run.rule.min_confidence_level ? (
          <Badge
            label={`Confidence ${CONFIDENCE_COPY[run.rule.min_confidence_level].label}`}
            className={CONFIDENCE_COPY[run.rule.min_confidence_level].className}
          />
        ) : null}
      </div>
      <p className="mt-4 text-xs uppercase tracking-widest text-muted">
        Required fields: {run.rule.required_fields.length > 0 ? run.rule.required_fields.join(", ") : "none"}
      </p>
    </section>
  );
}

function ResultTable({ run }: { run: ScreenerRun }): React.ReactElement {
  return (
    <section className="overflow-hidden rounded-md border border-muted/30 bg-white/[0.02]">
      <div className="grid grid-cols-[1fr_1fr] border-b border-muted/20 px-4 py-3 text-xs uppercase tracking-widest text-muted md:grid-cols-[1fr_1.2fr_2fr]">
        <span>Symbol</span>
        <span>Status / Gates</span>
        <span className="hidden md:block">Explanation</span>
      </div>
      {run.results.map((result) => (
        <article key={result.symbol} className="grid gap-3 border-b border-muted/10 px-4 py-4 text-sm last:border-b-0 md:grid-cols-[1fr_1.2fr_2fr]">
          <div>
            <p className="font-mono text-base">{result.symbol}</p>
            <Badge
              label={result.result_status === "included" ? "Included" : "Excluded"}
              className={
                result.result_status === "included"
                  ? "border-emerald-500/40 text-emerald-300"
                  : "border-red-500/40 text-red-300"
              }
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge label={COVERAGE_COPY[result.coverage_tier].label} className={COVERAGE_COPY[result.coverage_tier].className} />
            <Badge label={LIFECYCLE_COPY[result.lifecycle_status].label} className={LIFECYCLE_COPY[result.lifecycle_status].className} />
            <Badge label={FRESHNESS_COPY[result.freshness_state].label} className={FRESHNESS_COPY[result.freshness_state].className} />
            {result.completeness_state ? (
              <Badge label={COMPLETENESS_COPY[result.completeness_state].label} className={COMPLETENESS_COPY[result.completeness_state].className} />
            ) : null}
            {result.confidence_level ? (
              <Badge
                label={`Confidence ${CONFIDENCE_COPY[result.confidence_level].label}`}
                className={CONFIDENCE_COPY[result.confidence_level].className}
              />
            ) : null}
          </div>
          <div>
            <p className="text-sm text-fg">{result.explanation}</p>
            <ReasonList title="Exclusion reasons" items={result.exclusion_reasons} />
            <ReasonList title="Missing fields" items={result.missing_fields} />
            <ReasonList title="Caveats" items={result.caveats} />
          </div>
        </article>
      ))}
    </section>
  );
}

function EmptyState(): React.ReactElement {
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm">
      <p className="font-medium">No screener rows yet.</p>
      <p className="mt-2 text-muted">
        Run{" "}
        <code className="font-mono">
          uv run python -m scripts.screener --json run --builtin fundamentals-basic --from-watchlist
        </code>{" "}
        after V1-S1 and V1-S2 local snapshots are populated.
      </p>
    </section>
  );
}

function ErrorPanel({ error }: { error: string }): React.ReactElement {
  return (
    <section className="rounded-md border border-red-500/40 bg-red-500/[0.05] p-5 text-sm">
      <p className="font-medium text-red-300">Gagal membaca screener.</p>
      <p className="mt-2 text-muted">
        Pastikan migration dan snapshot lokal sudah siap:{" "}
        <code className="font-mono">uv run python -m scripts.migrate</code>
      </p>
      <pre className="mt-3 whitespace-pre-wrap text-xs text-red-200">{error}</pre>
    </section>
  );
}

function ReasonList({ title, items }: { title: string; items: string[] }): React.ReactElement | null {
  if (items.length === 0) return null;
  return (
    <div className="mt-3">
      <p className="text-xs uppercase tracking-widest text-muted">{title}</p>
      <ul className="mt-1 list-inside list-disc text-muted">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }): React.ReactElement {
  return (
    <div>
      <dt className="text-xs uppercase tracking-widest text-muted">{label}</dt>
      <dd className="mt-1 text-xl font-semibold text-fg">{value}</dd>
    </div>
  );
}

function Badge({ label, className }: { label: string; className: string }): React.ReactElement {
  return <span className={`rounded border px-2 py-1 text-xs uppercase tracking-widest ${className}`}>{label}</span>;
}
