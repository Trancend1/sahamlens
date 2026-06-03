import type {
  CompletenessState,
  ConfidenceLevel,
  CoverageTier,
  FundamentalSnapshotOverview,
  LifecycleStatus,
} from "@/lib/fundamentals";
import { RuntimeErrorState } from "./ui/RuntimeErrorState";

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
  overview: FundamentalSnapshotOverview | null;
  error?: string | null;
}

export function FundamentalSnapshotCard({ overview, error = null }: Props): React.ReactElement {
  const coverage = overview?.coverage ?? null;
  const fundamental = overview?.fundamental ?? null;
  const isRestricted =
    !coverage?.screener_eligible ||
    !fundamental ||
    fundamental.completeness_state !== "complete" ||
    fundamental.missing_fields.length > 0 ||
    ["low", "none"].includes(fundamental.confidence_level);

  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-widest text-muted">Fundamental Snapshot</p>
          <h2 className="mt-1 text-xl font-semibold">{overview?.symbol ?? "No symbol"}</h2>
        </div>
        <span
          className={`rounded border px-2 py-1 text-xs uppercase tracking-widest ${
            isRestricted ? "border-amber-500/40 text-amber-300" : "border-emerald-500/40 text-emerald-300"
          }`}
        >
          {isRestricted ? "Read-only" : "Usable"}
        </span>
      </div>

      {error ? (
        <div className="mt-4">
          <RuntimeErrorState
            title="Fundamental snapshot could not be loaded"
            message="The local fundamental snapshot command could not complete."
            details={error}
            recommendedCommand="uv run python -m scripts.runtime status --json"
          />
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        {coverage ? (
          <>
            <Badge label={COVERAGE_COPY[coverage.coverage_tier].label} className={COVERAGE_COPY[coverage.coverage_tier].className} />
            <Badge label={LIFECYCLE_COPY[coverage.lifecycle_status].label} className={LIFECYCLE_COPY[coverage.lifecycle_status].className} />
          </>
        ) : (
          <Badge label="Coverage unknown" className="border-muted/40 text-muted" />
        )}
        {fundamental ? (
          <>
            <Badge label={COMPLETENESS_COPY[fundamental.completeness_state].label} className={COMPLETENESS_COPY[fundamental.completeness_state].className} />
            <Badge label={`Confidence ${CONFIDENCE_COPY[fundamental.confidence_level].label}`} className={CONFIDENCE_COPY[fundamental.confidence_level].className} />
          </>
        ) : (
          <Badge label="Fundamental missing" className="border-red-500/40 text-red-300" />
        )}
      </div>

      {coverage?.eligibility_reason ? (
        <p className="mt-4 text-sm text-muted">{coverage.eligibility_reason}</p>
      ) : null}

      {fundamental ? (
        <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr]">
          <div>
            <p className="text-xs uppercase tracking-widest text-muted">
              {fundamental.period} / {fundamental.source}
            </p>
            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              {Object.entries(fundamental.data_fields).map(([key, value]) => (
                <Metric key={key} label={key} value={String(value)} />
              ))}
            </dl>
            {Object.keys(fundamental.data_fields).length === 0 ? (
              <p className="mt-3 text-sm text-muted">No usable fundamental fields yet.</p>
            ) : null}
          </div>
          <div className="rounded-md border border-muted/20 p-3 text-sm">
            <p className="font-medium">Caveats</p>
            {fundamental.caveat ? <p className="mt-2 text-muted">{fundamental.caveat}</p> : null}
            {fundamental.missing_fields.length > 0 ? (
              <p className="mt-2 text-muted">Missing: {fundamental.missing_fields.join(", ")}</p>
            ) : null}
            {!fundamental.caveat && fundamental.missing_fields.length === 0 ? (
              <p className="mt-2 text-muted">No missing required fields recorded.</p>
            ) : null}
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted">
          No local fundamental snapshot. Ingest one with{" "}
          <code className="font-mono">uv run python -m scripts.fundamentals ingest</code>.
        </p>
      )}
    </section>
  );
}

function Badge({ label, className }: { label: string; className: string }): React.ReactElement {
  return <span className={`rounded border px-2 py-1 text-xs uppercase tracking-widest ${className}`}>{label}</span>;
}

function Metric({ label, value }: { label: string; value: string }): React.ReactElement {
  return (
    <div>
      <dt className="text-xs uppercase tracking-widest text-muted">{label}</dt>
      <dd className="mt-1 font-mono text-fg">{value}</dd>
    </div>
  );
}
