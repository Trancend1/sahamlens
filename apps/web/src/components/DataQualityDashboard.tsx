import Link from "next/link";
import { EmptyState as SharedEmptyState } from "@/components/ui/EmptyState";
import { RuntimeErrorState } from "@/components/ui/RuntimeErrorState";
import { ProviderHealthRefresh } from "@/components/ProviderHealthRefresh";
import type { DataQualityOverview, FreshnessState, ProviderHealthSnapshot } from "@/lib/dataQuality";
import type { RuntimeErrorInfo } from "@/lib/pythonRunner";
import type { RuntimeStatus } from "@/lib/runtime";

const STATE_COPY: Record<FreshnessState, { label: string; className: string; note: string }> = {
  fresh: {
    label: "Fresh",
    className: "border-emerald-500/40 text-emerald-300",
    note: "Usable for dependent flows.",
  },
  delayed: {
    label: "Delayed",
    className: "border-sky-500/40 text-sky-300",
    note: "Usable with caveat.",
  },
  stale: {
    label: "Stale",
    className: "border-amber-500/40 text-amber-300",
    note: "Review screener output with caution until data is refreshed.",
  },
  failed: {
    label: "Failed",
    className: "border-red-500/40 text-red-300",
    note: "Provider data could not be refreshed. Results may be incomplete.",
  },
  partial: {
    label: "Partial",
    className: "border-yellow-500/40 text-yellow-200",
    note: "Some coverage is missing.",
  },
  unknown: {
    label: "Unknown",
    className: "border-muted/40 text-muted",
    note: "No reliable source timestamp.",
  },
};

interface Props {
  overview: DataQualityOverview | null;
  error: RuntimeErrorInfo | null;
  runtimeStatus?: RuntimeStatus | null;
  runtimeError?: RuntimeErrorInfo | null;
}

export function DataQualityDashboard({
  overview,
  error,
  runtimeStatus = null,
  runtimeError = null,
}: Props): React.ReactElement {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">
          <Link href="/" className="hover:text-fg">
            SahamLens
          </Link>{" "}
          / V1-S1
        </p>
        <h1 className="mt-1 text-3xl font-semibold">Data Quality</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Provider health, freshness, coverage, and runtime readiness before using dependent
          decision-support workflows.
        </p>
      </header>

      <ProviderHealthRefresh />

      {error ? <ErrorPanel error={error} /> : null}
      <RuntimeReadiness status={runtimeStatus} error={runtimeError} />

      {overview ? (
        <>
          <Summary overview={overview} />
          {overview.providers.length === 0 ? <EmptyState /> : <ProviderList providers={overview.providers} />}
          <FreshnessLegend />
        </>
      ) : null}
    </main>
  );
}

function Summary({ overview }: { overview: DataQualityOverview }): React.ReactElement {
  const items = [
    ["Providers", overview.provider_count],
    ["Failed", overview.failed_provider_count],
    ["Stale", overview.stale_provider_count],
    ["Restricted", overview.restricted_provider_count],
    ["Coverage", overview.total_coverage_count],
  ] as const;
  return (
    <section className="grid gap-3 sm:grid-cols-5">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-md border border-muted/30 bg-white/[0.02] p-4">
          <p className="text-xs uppercase tracking-widest text-muted">{label}</p>
          <p className="mt-2 text-2xl font-semibold">{value}</p>
        </div>
      ))}
    </section>
  );
}

function EmptyState(): React.ReactElement {
  return (
    <SharedEmptyState
      title="Provider health has not been checked yet"
      description="Refresh provider health after migrations and watchlist setup so dependent pages can show freshness and coverage caveats."
      actionLabel="Refresh provider health"
      actionHref="/data-quality"
    />
  );
}

function RuntimeReadiness({
  status,
  error,
}: {
  status: RuntimeStatus | null;
  error: RuntimeErrorInfo | null;
}): React.ReactElement {
  if (error) {
    return (
      <RuntimeErrorState
        title="Runtime not ready"
        message={error.message}
        details={error.details}
      />
    );
  }

  if (!status) {
    return (
      <SharedEmptyState
        title="Runtime Readiness"
        description="Runtime status is not available yet. Check the local runtime before debugging page-level data."
        actionLabel="Check runtime status"
        actionHref="/data-quality"
      />
    );
  }

  const ready = status.schema_status === "ready";
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-medium">Runtime Readiness</p>
          <p className="mt-1 text-xs uppercase tracking-widest text-muted">
            {status.schema_status} / {status.ok ? "ok" : "needs attention"}
          </p>
        </div>
        <span
          className={`rounded border px-2 py-1 text-xs uppercase tracking-widest ${
            ready ? "border-emerald-500/40 text-emerald-300" : "border-amber-500/40 text-amber-300"
          }`}
        >
          {ready ? "Ready" : "Not Ready"}
        </span>
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <Metric label="Local DB" value={status.db_path ? "configured" : "not configured"} />
        <Metric label="Applied" value={status.applied_migrations.length} />
        <Metric label="Pending" value={status.pending_migrations.length} />
      </dl>
      {status.missing_tables.length > 0 ? (
        <p className="mt-3 text-amber-200">
          Missing tables: {status.missing_tables.slice(0, 6).join(", ")}
          {status.missing_tables.length > 6 ? "..." : ""}
        </p>
      ) : null}
      {status.recommended_commands.length > 0 ? (
        <Link
          href="/data-quality"
          className="mt-3 inline-flex rounded-md bg-accent px-4 py-2 text-xs font-medium text-white hover:opacity-90"
        >
          Check runtime status
        </Link>
      ) : null}
      {status.warnings.length > 0 ? (
        <ul className="mt-3 list-inside list-disc text-sm text-muted">
          {status.warnings.slice(0, 5).map((warning) => (
            <li key={`${warning.code}-${warning.message}`}>{warning.message}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function ErrorPanel({ error }: { error: RuntimeErrorInfo }): React.ReactElement {
  const isSchemaError = error.code === "missing_table" || error.code === "schema_stale";
  return (
    <RuntimeErrorState
      title={isSchemaError ? "Migration required" : "Data quality could not be loaded"}
      message={error.message}
      details={error.details}
    />
  );
}

function ProviderList({ providers }: { providers: ProviderHealthSnapshot[] }): React.ReactElement {
  return (
    <section className="grid gap-3">
      {providers.map((provider) => (
        <ProviderCard key={`${provider.provider_name}-${provider.source_type}`} provider={provider} />
      ))}
    </section>
  );
}

function ProviderCard({ provider }: { provider: ProviderHealthSnapshot }): React.ReactElement {
  const state = STATE_COPY[provider.freshness_state];
  return (
    <article
      className="rounded-md border border-muted/30 bg-white/[0.02] p-5"
      data-state={provider.freshness_state}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-lg">{provider.provider_name}</p>
          <p className="mt-1 text-xs uppercase tracking-widest text-muted">
            {provider.source_type} / {provider.provider_trust_tier}
          </p>
        </div>
        <span className={`rounded border px-2 py-1 text-xs uppercase tracking-widest ${state.className}`}>
          {state.label}
        </span>
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-4">
        <Metric label="Coverage" value={provider.coverage_count ?? "n/a"} />
        <Metric label="Failures" value={provider.consecutive_failure_count} />
        <Metric label="Updated" value={formatDate(provider.updated_at)} />
        <Metric
          label="Dependent flows"
          value={provider.supports_dependent_flows ? "enabled" : "restricted"}
        />
      </dl>
      <p className="mt-4 text-sm text-muted">{state.note}</p>
      {provider.last_failure_reason ? (
        <p className="mt-2 text-sm text-red-200">{provider.last_failure_reason}</p>
      ) : null}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string | number }): React.ReactElement {
  return (
    <div>
      <dt className="text-xs uppercase tracking-widest text-muted">{label}</dt>
      <dd className="mt-1 text-fg">{value}</dd>
    </div>
  );
}

function FreshnessLegend(): React.ReactElement {
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <h2 className="text-sm font-medium">Freshness states</h2>
      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        {(Object.keys(STATE_COPY) as FreshnessState[]).map((state) => (
          <div key={state} data-state={state} className="text-sm">
            <span className={`rounded border px-2 py-1 text-xs uppercase ${STATE_COPY[state].className}`}>
              {STATE_COPY[state].label}
            </span>
            <p className="mt-2 text-muted">{STATE_COPY[state].note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toISOString().slice(0, 16).replace("T", " ");
  } catch {
    return iso;
  }
}
