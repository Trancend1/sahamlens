import type { IndicatorKey } from "./indicatorMeta";
import { runPython } from "./pythonRunner";

export interface OhlcvRow {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface IndicatorSeriesPoint {
  date: string;
  value: number;
}

export interface StockDetail {
  symbol: string;
  ohlcv: OhlcvRow[];
  indicators_series: Record<IndicatorKey, IndicatorSeriesPoint[]>;
  indicators_latest: Partial<Record<IndicatorKey, number>>;
  first_date: string | null;
  last_date: string | null;
}

export async function fetchStockDetail(symbol: string, days = 365): Promise<StockDetail> {
  const { data } = await runPython<StockDetail>("scripts.dump_stock_detail", {
    args: ["--symbol", symbol, "--days", String(days)],
    timeoutMs: 30_000,
  });
  return data;
}
