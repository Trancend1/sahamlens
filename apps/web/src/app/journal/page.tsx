import Link from "next/link";
import { fetchPlans, type TradePlan, type TradeStatus } from "@/lib/journal";

export const dynamic = "force-dynamic";

const STATUS_STYLE: Record<TradeStatus, string> = {
  planned: "text-accent border-accent/40",
  open: "text-yellow-400 border-yellow-400/40",
  closed: "text-muted border-muted/40",
  skipped: "text-muted/50 border-muted/30",
};

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

export default async function JournalPage() {
  let plans: TradePlan[] = [];
  let error: string | null = null;

  try {
    plans = await fetchPlans();
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <header className="flex items-end justify-between">
        <div>
          <p className="text-sm uppercase tracking-widest text-muted">
            <Link href="/" className="hover:text-fg">SahamLens</Link> · S5
          </p>
          <h1 className="mt-1 text-3xl font-semibold">Trade Journal</h1>
          <p className="mt-2 text-sm text-muted">{plans.length} plan tersimpan</p>
        </div>
        <Link
          href="/journal/new"
          className="rounded border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10"
        >
          + Plan Baru
        </Link>
      </header>

      {error ? (
        <section className="rounded-md border border-red-500/40 bg-red-500/[0.05] p-5 text-sm">
          <p className="font-medium text-red-300">Gagal membaca journal.</p>
          <pre className="mt-3 whitespace-pre-wrap text-xs text-red-200">{error}</pre>
        </section>
      ) : plans.length === 0 ? (
        <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm">
          <p>Belum ada trade plan.</p>
          <p className="mt-2 text-muted">
            <Link href="/journal/new" className="text-accent underline">
              Buat plan pertama
            </Link>
          </p>
        </section>
      ) : (
        <ul className="divide-y divide-muted/20 rounded-md border border-muted/30 bg-white/[0.02]">
          {plans.map((p) => (
            <li key={p.id} className="flex items-center justify-between gap-4 px-5 py-3">
              <div className="flex min-w-0 flex-col gap-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm text-fg">{p.symbol}</span>
                  <span className="text-xs text-muted">{p.setup_type}</span>
                </div>
                <p className="truncate text-xs text-muted/70">{p.thesis}</p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <PnlBadge plan={p} />
                <span
                  className={`rounded border px-2 py-0.5 text-xs ${STATUS_STYLE[p.status] ?? ""}`}
                >
                  {p.status}
                </span>
                <span className="text-xs text-muted">{formatDate(p.created_at)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}

    </main>
  );
}
