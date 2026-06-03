import Link from "next/link";
import { FreshnessBadge } from "@/components/FreshnessBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { RuntimeErrorState } from "@/components/ui/RuntimeErrorState";
import { fetchWatchlist, type WatchlistEntry } from "@/lib/watchlist";

export const dynamic = "force-dynamic";

export default async function WatchlistPage() {
  let entries: WatchlistEntry[] = [];
  let error: string | null = null;
  try {
    entries = await fetchWatchlist();
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">
          <Link href="/" className="hover:text-fg">SahamLens</Link> / Watchlist
        </p>
        <h1 className="mt-1 text-3xl font-semibold">Watchlist</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          {entries.length} ticker tracked locally. The watchlist anchors provider refreshes,
          coverage checks, screener runs, and review workflows.
        </p>
      </header>

      {error ? (
        <RuntimeErrorState
          title="Watchlist could not be loaded"
          message="The local watchlist command could not complete."
          details={error}
          recommendedCommand="uv run python -m scripts.runtime status --json"
        />
      ) : entries.length === 0 ? (
        <EmptyState
          title="No tickers in your watchlist yet"
          description="Add your first ticker before refreshing provider health, coverage, fundamentals, or screener runs."
          actionLabel="Add your first ticker"
          command="uv run python -m scripts.watchlist seed"
        />
      ) : (
        <ul className="divide-y divide-muted/20 rounded-md border border-muted/30 bg-white/[0.02]">
          {entries.map((entry) => (
            <li
              key={entry.symbol}
              className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-baseline sm:justify-between"
            >
              <div className="flex flex-wrap items-baseline gap-3">
                <Link
                  href={`/stocks/${shortSymbol(entry.symbol)}`}
                  className="font-mono text-base text-fg hover:text-accent hover:underline"
                >
                  {entry.symbol}
                </Link>
                {entry.tag ? (
                  <span className="rounded border border-accent/40 px-2 py-0.5 text-xs text-accent">
                    {entry.tag}
                  </span>
                ) : null}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {entry.fetched_at ? <FreshnessBadge iso={entry.fetched_at} /> : null}
                <span className="text-xs text-muted">added {formatDate(entry.added_at)}</span>
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

function shortSymbol(symbol: string): string {
  return symbol.replace(/\.JK$/i, "");
}
