import Link from "next/link";
import { EmptyState } from "@/components/ui/EmptyState";
import { RuntimeErrorState } from "@/components/ui/RuntimeErrorState";
import { fetchPlans, type TradePlan, type TradeStatus } from "@/lib/journal";

export const dynamic = "force-dynamic";

const STATUS_STYLE: Record<TradeStatus, string> = {
  planned: "text-accent border-accent/40",
  open: "text-yellow-400 border-yellow-400/40",
  closed: "text-muted border-muted/40",
  skipped: "text-muted/50 border-muted/30",
};

export default async function JournalPage() {
  let plans: TradePlan[] = [];
  let error: string | null = null;

  try {
    plans = await fetchPlans();
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-6 py-10">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm uppercase tracking-widest text-muted">
            <Link href="/" className="hover:text-fg">SahamLens</Link> / Journal
          </p>
          <h1 className="mt-1 text-3xl font-semibold">Trade Journal</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            {plans.length} plan stored locally. Journal entries feed Weekly Review and
            Strategy Rules.
          </p>
        </div>
        <Link
          href="/journal/new"
          className="rounded border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10"
        >
          Add journal entry
        </Link>
      </header>

      {error ? (
        <RuntimeErrorState
          title="Journal could not be loaded"
          message="The local journal command could not complete."
          details={error}
          recommendedCommand="uv run python -m scripts.runtime status --json"
        />
      ) : plans.length === 0 ? (
        <EmptyState
          title="No journal entries yet"
          description="Add a journal entry with thesis, risk, invalidation, and emotion notes before generating Weekly Review or Strategy Rule evaluations."
          actionLabel="Add journal entry"
          actionHref="/journal/new"
        />
      ) : (
        <ul className="divide-y divide-muted/20 rounded-md border border-muted/30 bg-white/[0.02]">
          {plans.map((plan) => (
            <li
              key={plan.id}
              className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex min-w-0 flex-col gap-0.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-sm text-fg">{plan.symbol}</span>
                  <span className="text-xs text-muted">{plan.setup_type}</span>
                </div>
                <p className="truncate text-xs text-muted/70">{plan.thesis}</p>
              </div>
              <div className="flex shrink-0 flex-wrap items-center gap-3">
                <PnlBadge plan={plan} />
                <span
                  className={`rounded border px-2 py-0.5 text-xs ${STATUS_STYLE[plan.status] ?? ""}`}
                >
                  {plan.status}
                </span>
                <span className="text-xs text-muted">{formatDate(plan.created_at)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toISOString().slice(0, 10);
  } catch {
    return iso;
  }
}

function PnlBadge({ plan }: { plan: TradePlan }) {
  if (plan.status !== "closed" || plan.result_rupiah === null) return null;
  const sign = plan.result_rupiah >= 0 ? "+" : "";
  const cls = plan.result_rupiah >= 0 ? "text-green-400" : "text-red-400";
  return (
    <span className={`font-mono text-xs ${cls}`}>
      {sign}
      {plan.result_rupiah.toLocaleString("id-ID")}
    </span>
  );
}
