import Link from "next/link";
import { ChatPanel } from "@/components/ChatPanel";
import { FundamentalSnapshotCard } from "@/components/FundamentalSnapshotCard";
import { IndicatorCard } from "@/components/IndicatorCard";
import { NewsSection } from "@/components/NewsSection";
import { StockBriefPanel } from "@/components/StockBriefPanel";
import { StockChart } from "@/components/StockChart";
import { StockFreshnessBar } from "@/components/StockFreshnessBar";
import { fetchFundamentalSnapshot, type FundamentalSnapshotOverview } from "@/lib/fundamentals";
import { INDICATOR_KEYS, type IndicatorKey } from "@/lib/indicatorMeta";
import { fetchStockDetail, type StockDetail } from "@/lib/stockDetail";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ symbol: string }>;
}

export default async function StockDetailPage({ params }: PageProps) {
  const { symbol } = await params;
  let detail: StockDetail | null = null;
  let fundamental: FundamentalSnapshotOverview | null = null;
  let fundamentalError: string | null = null;
  let error: string | null = null;

  try {
    detail = await fetchStockDetail(symbol, 365);
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  if (!error) {
    try {
      fundamental = await fetchFundamentalSnapshot(symbol);
    } catch (err) {
      fundamentalError = err instanceof Error ? err.message : String(err);
    }
  }

  if (error) {
    return (
      <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
        <Header symbol={symbol.toUpperCase()} />
        <section className="rounded-md border border-red-500/40 bg-red-500/[0.05] p-5 text-sm">
          <p className="font-medium text-red-300">Gagal load data {symbol.toUpperCase()}.</p>
          <p className="mt-2 text-muted">
            Pastikan price_history & indicator_cache sudah di-seed:
          </p>
          <pre className="mt-2 whitespace-pre-wrap text-xs text-muted">
            uv run python -m scripts.ingest_prices --symbols {symbol.toUpperCase()} --days 365
            {"\n"}uv run python -m scripts.calculate_indicators --symbols {symbol.toUpperCase()}
          </pre>
          <pre className="mt-3 whitespace-pre-wrap text-xs text-red-200">{error}</pre>
        </section>
      </main>
    );
  }

  if (!detail || detail.ohlcv.length === 0) {
    return (
      <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
        <Header symbol={symbol.toUpperCase()} />
        <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm">
          <p>Belum ada data harga untuk {symbol.toUpperCase()}.</p>
          <pre className="mt-2 whitespace-pre-wrap text-xs text-muted">
            uv run python -m scripts.ingest_prices --symbols {symbol.toUpperCase()} --days 365
            {"\n"}uv run python -m scripts.calculate_indicators --symbols {symbol.toUpperCase()}
          </pre>
        </section>
        <FundamentalSnapshotCard overview={fundamental} error={fundamentalError} />
      </main>
    );
  }

  const currentClose = lastClose(detail.ohlcv);
  const maSeries: Partial<Record<string, typeof detail.indicators_series[IndicatorKey]>> = {
    ma_5: detail.indicators_series.ma_5,
    ma_10: detail.indicators_series.ma_10,
    ma_15: detail.indicators_series.ma_15,
    ma_50: detail.indicators_series.ma_50,
    ma_200: detail.indicators_series.ma_200,
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
      <Header
        symbol={detail.symbol}
        currentClose={currentClose}
        firstDate={detail.first_date}
        lastDate={detail.last_date}
      />

      <StockFreshnessBar lastDate={detail.last_date} />

      <FundamentalSnapshotCard overview={fundamental} error={fundamentalError} />

      <section>
        <StockChart
          ohlcv={detail.ohlcv}
          maSeries={maSeries}
          rsiSeries={detail.indicators_series.rsi_14}
          macdLine={detail.indicators_series.macd_line}
          macdSignal={detail.indicators_series.macd_signal}
          macdHist={detail.indicators_series.macd_hist}
        />
      </section>

      <NewsSection items={detail.news_recent ?? []} symbol={detail.symbol} />

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {INDICATOR_KEYS.map((key) => (
          <IndicatorCard
            key={key}
            indicator={key}
            value={detail.indicators_latest[key] ?? null}
            currentPrice={currentClose}
            computedAt={detail.last_date}
          />
        ))}
      </section>

      <hr className="border-muted/20" />

      <StockBriefPanel symbol={detail.symbol} />

      <ChatPanel symbol={detail.symbol} />

    </main>
  );
}

interface HeaderProps {
  symbol: string;
  currentClose?: number | null;
  firstDate?: string | null;
  lastDate?: string | null;
}

function Header({ symbol, currentClose, firstDate, lastDate }: HeaderProps) {
  return (
    <header className="flex flex-col gap-1">
      <div className="flex items-baseline gap-3">
        <p className="text-sm uppercase tracking-widest text-muted">SahamLens · Stock detail</p>
        <Link href="/watchlist" className="text-xs text-accent hover:underline">
          ← watchlist
        </Link>
      </div>
      <div className="flex items-baseline justify-between gap-4">
        <h1 className="text-3xl font-semibold font-mono">{symbol}</h1>
        {currentClose != null ? (
          <span className="font-mono text-2xl tabular-nums">
            {new Intl.NumberFormat("id-ID").format(Math.round(currentClose))}
          </span>
        ) : null}
      </div>
      {firstDate && lastDate ? (
        <p className="text-xs text-muted">
          Series: {firstDate} → {lastDate}
        </p>
      ) : null}
    </header>
  );
}

function lastClose(ohlcv: StockDetail["ohlcv"]): number | null {
  for (let i = ohlcv.length - 1; i >= 0; i--) {
    const row = ohlcv[i];
    if (row?.close != null) return row.close;
  }
  return null;
}
