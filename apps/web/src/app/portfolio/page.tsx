import Link from "next/link";
import { fetchPositions, type PortfolioPosition } from "@/lib/portfolio";
import { fetchStockDetail } from "@/lib/stockDetail";

export const dynamic = "force-dynamic";

export default async function PortfolioPage() {
  let positions: PortfolioPosition[] = [];
  let error: string | null = null;

  try {
    positions = await fetchPositions();
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  const closePrices =
    positions.length > 0 ? await loadClosePrices(positions.map((p) => p.symbol)) : {};

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-6 py-10">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-widest text-muted">
            <Link href="/" className="hover:text-fg">SahamLens</Link> · Portfolio
          </p>
          <h1 className="mt-1 text-3xl font-semibold">Posisi Aktual</h1>
          <p className="mt-2 text-sm text-muted">
            {positions.length} posisi · harga dari price_history lokal
          </p>
        </div>
        <Link
          href="/portfolio/import"
          className="rounded border border-accent/40 px-3 py-1.5 text-sm text-accent hover:bg-accent/10"
        >
          Import CSV
        </Link>
      </header>

      {error ? (
        <section className="rounded-md border border-red-500/40 bg-red-500/[0.05] p-5 text-sm">
          <p className="font-medium text-red-300">Gagal membaca posisi.</p>
          <pre className="mt-3 whitespace-pre-wrap text-xs text-red-200">{error}</pre>
        </section>
      ) : positions.length === 0 ? (
        <section className="rounded-md border border-muted/30 bg-white/[0.02] p-8 text-center text-sm">
          <p className="text-muted">Belum ada posisi.</p>
          <Link
            href="/portfolio/import"
            className="mt-3 inline-block text-accent underline hover:no-underline"
          >
            Import CSV untuk mulai
          </Link>
        </section>
      ) : (
        <div className="overflow-x-auto rounded-md border border-muted/30">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-muted/30 text-xs uppercase tracking-widest text-muted">
                <th className="px-4 py-3 text-left">Symbol</th>
                <th className="px-4 py-3 text-right">Lot</th>
                <th className="px-4 py-3 text-right">Avg Beli</th>
                <th className="px-4 py-3 text-right">Harga Kini</th>
                <th className="px-4 py-3 text-right">P&amp;L %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-muted/20">
              {positions.map((p) => {
                const close = closePrices[p.symbol] ?? null;
                const pnlPct =
                  close != null ? ((close - p.avg_price) / p.avg_price) * 100 : null;
                return (
                  <tr key={p.symbol} className="hover:bg-white/[0.02]">
                    <td className="px-4 py-3">
                      <Link
                        href={`/stocks/${p.symbol.replace(/\.JK$/i, "")}`}
                        className="font-mono text-fg hover:text-accent hover:underline"
                      >
                        {p.symbol}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">{p.lots}</td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums">
                      {formatRp(p.avg_price)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums">
                      {close != null ? (
                        formatRp(close)
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {pnlPct != null ? (
                        <span className={pnlPct >= 0 ? "text-emerald-400" : "text-red-400"}>
                          {pnlPct >= 0 ? "+" : ""}
                          {pnlPct.toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

async function loadClosePrices(symbols: string[]): Promise<Record<string, number>> {
  const results: Record<string, number> = {};
  await Promise.allSettled(
    symbols.map(async (symbol) => {
      try {
        const short = symbol.replace(/\.JK$/i, "");
        const detail = await fetchStockDetail(short, 5);
        for (let i = detail.ohlcv.length - 1; i >= 0; i--) {
          const row = detail.ohlcv[i];
          if (row != null && row.close != null) {
            results[symbol] = row.close;
            break;
          }
        }
      } catch {
        // no close available — column shows —
      }
    }),
  );
  return results;
}

function formatRp(n: number): string {
  return new Intl.NumberFormat("id-ID").format(Math.round(n));
}
