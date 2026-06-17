import Link from "next/link";
import { ChatPanel } from "@/components/ChatPanel";
import { FundamentalSnapshotCard } from "@/components/FundamentalSnapshotCard";
import { IndicatorCard } from "@/components/IndicatorCard";
import { LlmStatusBadge } from "@/components/LlmStatusBadge";
import { NewsSection } from "@/components/NewsSection";
import { StockBriefPanel } from "@/components/StockBriefPanel";
import { StockChart } from "@/components/StockChart";
import { StockDetailActions } from "@/components/StockDetailActions";
import { StockFreshnessBar } from "@/components/StockFreshnessBar";
import { EmptyState } from "@/components/ui/EmptyState";
import { RuntimeErrorState } from "@/components/ui/RuntimeErrorState";
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
        <RuntimeErrorState
          title={`Stock data could not be loaded for ${symbol.toUpperCase()}`}
          message="The local stock-detail command could not complete."
          details={error}
        />
      </main>
    );
  }

  if (!detail || detail.ohlcv.length === 0) {
    return (
      <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
        <Header symbol={symbol.toUpperCase()} />
        <EmptyState
          title={`No local price data for ${symbol.toUpperCase()}`}
          description="Ingest price history before using charts, indicators, or freshness review for this ticker."
          actionLabel="Refresh price data"
        />
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

      <StockDetailActions symbol={detail.symbol} />

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

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted">
          AI Analysis
        </h2>
        <LlmStatusBadge compact />
      </div>

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
    <header className="flex flex-col gap-2">
      <div className="flex flex-wrap items-baseline gap-3">
        <p className="text-sm uppercase tracking-widest text-muted">SahamLens / Stock detail</p>
        <Link href="/watchlist" className="text-xs text-accent hover:underline">
          Back to watchlist
        </Link>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
        <h1 className="font-mono text-3xl font-semibold">{symbol}</h1>
        {currentClose != null ? (
          <span className="font-mono text-2xl tabular-nums">
            {new Intl.NumberFormat("id-ID").format(Math.round(currentClose))}
          </span>
        ) : null}
      </div>
      {firstDate && lastDate ? (
        <p className="text-xs text-muted">
          Series: {firstDate} to {lastDate}
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
