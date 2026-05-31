import Link from "next/link";
import type { DataQualityOverview, FreshnessState, ProviderHealthSnapshot } from "@/lib/dataQuality";

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
    note: "Restrict screener and price alerts.",
  },
  failed: {
    label: "Failed",
    className: "border-red-500/40 text-red-300",
    note: "Provider failed; use failure/freshness alerts only.",
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
  error: string | null;
}

export function DataQualityDashboard({ overview, error }: Props): React.ReactElement {
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
          Provider health, freshness, coverage, and dependent-flow readiness before screener
          or alerts.
        </p>
      </header>

      {error ? <ErrorPanel error={error} /> : null}

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
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm">
      <p className="font-medium">Belum ada provider health snapshot.</p>
      <p className="mt-2 text-muted">
        Run{" "}
        <code className="font-mono">
          uv run python -m scripts.provider_health refresh-yfinance --from-watchlist
        </code>{" "}
        after migrations and watchlist are ready.
      </p>
    </section>
  );
}

function ErrorPanel({ error }: { error: string }): React.ReactElement {
  return (
    <section className="rounded-md border border-red-500/40 bg-red-500/[0.05] p-5 text-sm">
      <p className="font-medium text-red-300">Gagal membaca data quality.</p>
      <p className="mt-2 text-muted">
        Pastikan migration terbaru sudah jalan:{" "}
        <code className="font-mono">uv run python -m scripts.migrate</code>
      </p>
      <pre className="mt-3 whitespace-pre-wrap text-xs text-red-200">{error}</pre>
    </section>
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
