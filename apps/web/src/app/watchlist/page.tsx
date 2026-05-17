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
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">SahamLens · S1</p>
        <h1 className="mt-1 text-3xl font-semibold">Watchlist</h1>
        <p className="mt-2 text-sm text-muted">
          {entries.length} ticker · read-only (mutasi via CLI: `uv run python -m scripts.watchlist`).
        </p>
      </header>

      {error ? (
        <section className="rounded-md border border-red-500/40 bg-red-500/[0.05] p-5 text-sm">
          <p className="font-medium text-red-300">Gagal membaca watchlist.</p>
          <p className="mt-2 text-muted">
            Pastikan DuckDB ada dan watchlist sudah di-seed:{" "}
            <code className="font-mono">uv run python -m scripts.watchlist seed</code>
          </p>
          <pre className="mt-3 whitespace-pre-wrap text-xs text-red-200">{error}</pre>
        </section>
      ) : entries.length === 0 ? (
        <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm">
          <p>Watchlist kosong.</p>
          <p className="mt-2 text-muted">
            Seed default: <code className="font-mono">uv run python -m scripts.watchlist seed</code>
          </p>
        </section>
      ) : (
        <ul className="divide-y divide-muted/20 rounded-md border border-muted/30 bg-white/[0.02]">
          {entries.map((e) => (
            <li key={e.symbol} className="flex items-baseline justify-between gap-4 px-5 py-3">
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-base">{e.symbol}</span>
                {e.tag ? (
                  <span className="rounded border border-accent/40 px-2 py-0.5 text-xs text-accent">
                    {e.tag}
                  </span>
                ) : null}
              </div>
              <span className="text-xs text-muted">added {formatDate(e.added_at)}</span>
            </li>
          ))}
        </ul>
      )}

      <footer className="text-xs text-muted">
        Personal learning & analysis tool. Bukan investment advice. AI explains, user decides.
      </footer>
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
