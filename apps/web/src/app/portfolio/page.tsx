import Link from "next/link";
import { DataTableWrapper } from "@/components/ui/DataTableWrapper";
import { EmptyState } from "@/components/ui/EmptyState";
import { RuntimeErrorState } from "@/components/ui/RuntimeErrorState";
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
    positions.length > 0 ? await loadClosePrices(positions.map((position) => position.symbol)) : {};

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 px-6 py-10">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm uppercase tracking-widest text-muted">
            <Link href="/" className="hover:text-fg">SahamLens</Link> / Portfolio
          </p>
          <h1 className="mt-1 text-3xl font-semibold">Portfolio</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            {positions.length} local position(s). Prices use available local price history and may
            be incomplete.
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
        <RuntimeErrorState
          title="Portfolio could not be loaded"
          message="The local portfolio command could not complete."
          details={error}
        />
      ) : positions.length === 0 ? (
        <EmptyState
          title="No portfolio positions yet"
          description="Import a local CSV when you want portfolio context. This page is optional for V1 decision support."
          actionLabel="Import CSV"
          actionHref="/portfolio/import"
        />
      ) : (
        <DataTableWrapper>
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-muted/30 text-xs uppercase tracking-widest text-muted">
                <th className="px-4 py-3 text-left">Symbol</th>
                <th className="px-4 py-3 text-right">Lot</th>
                <th className="px-4 py-3 text-right">Average Cost</th>
                <th className="px-4 py-3 text-right">Latest Price</th>
                <th className="px-4 py-3 text-right">P&amp;L %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-muted/20">
              {positions.map((position) => {
                const close = closePrices[position.symbol] ?? null;
                const pnlPct =
                  close != null ? ((close - position.avg_price) / position.avg_price) * 100 : null;
                return (
                  <tr key={position.symbol} className="hover:bg-white/[0.02]">
                    <td className="px-4 py-3">
                      <Link
                        href={`/stocks/${position.symbol.replace(/\.JK$/i, "")}`}
                        className="font-mono text-fg hover:text-accent hover:underline"
                      >
                        {position.symbol}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">{position.lots}</td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums">
                      {formatRp(position.avg_price)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums">
                      {close != null ? formatRp(close) : <span className="text-muted">n/a</span>}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {pnlPct != null ? (
                        <span className={pnlPct >= 0 ? "text-emerald-400" : "text-red-400"}>
                          {pnlPct >= 0 ? "+" : ""}
                          {pnlPct.toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-muted">n/a</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </DataTableWrapper>
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
        // Missing local price history leaves the table cell as n/a.
      }
    }),
  );
  return results;
}

function formatRp(value: number): string {
  return new Intl.NumberFormat("id-ID").format(Math.round(value));
}
