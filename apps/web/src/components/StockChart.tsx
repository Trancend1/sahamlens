"use client";

import {
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  LineSeries,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type Time,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import type {
  IndicatorSeriesPoint,
  OhlcvRow,
} from "@/lib/stockDetail";

const CHART_BG = "#0b0f17";
const CHART_FG = "#e5ecf3";
const CHART_GRID = "#1a2230";
const UP = "#16a34a";
const DOWN = "#dc2626";
const MA_COLORS: Record<string, string> = {
  ma_5: "#8aa6c9",
  ma_10: "#6b8eb5",
  ma_15: "#4f78a3",
  ma_50: "#e5a85d",
  ma_200: "#a16ad9",
};
const RSI_COLOR = "#e5a85d";
const RSI_REF = "#7a8699";
const MACD_LINE_COLOR = "#8aa6c9";
const MACD_SIGNAL_COLOR = "#e5a85d";

interface StockChartProps {
  ohlcv: OhlcvRow[];
  maSeries: Partial<Record<string, IndicatorSeriesPoint[]>>;
  rsiSeries: IndicatorSeriesPoint[];
  macdLine: IndicatorSeriesPoint[];
  macdSignal: IndicatorSeriesPoint[];
  macdHist: IndicatorSeriesPoint[];
}

export function StockChart(props: StockChartProps): React.ReactElement {
  const priceRef = useRef<HTMLDivElement>(null);
  const rsiRef = useRef<HTMLDivElement>(null);
  const macdRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!priceRef.current || !rsiRef.current || !macdRef.current) return;

    const priceChart = createChart(priceRef.current, baseOptions(priceRef.current.clientWidth, 360));
    const rsiChart = createChart(rsiRef.current, baseOptions(rsiRef.current.clientWidth, 140));
    const macdChart = createChart(macdRef.current, baseOptions(macdRef.current.clientWidth, 160));

    const candle = priceChart.addSeries(CandlestickSeries, {
      upColor: UP,
      downColor: DOWN,
      borderUpColor: UP,
      borderDownColor: DOWN,
      wickUpColor: UP,
      wickDownColor: DOWN,
    });
    candle.setData(toCandleData(props.ohlcv));

    const maSeriesByKey: Array<{ key: string; series: ISeriesApi<"Line"> }> = [];
    for (const [key, color] of Object.entries(MA_COLORS)) {
      const data = props.maSeries[key];
      if (!data || data.length === 0) continue;
      const s = priceChart.addSeries(LineSeries, {
        color,
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      s.setData(toLineData(data));
      maSeriesByKey.push({ key, series: s });
    }

    const rsi = rsiChart.addSeries(LineSeries, {
      color: RSI_COLOR,
      lineWidth: 1,
      priceFormat: { type: "price", precision: 2, minMove: 0.01 },
    });
    rsi.setData(toLineData(props.rsiSeries));
    rsi.createPriceLine({
      price: 70,
      color: RSI_REF,
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: true,
      title: "70",
    });
    rsi.createPriceLine({
      price: 30,
      color: RSI_REF,
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: true,
      title: "30",
    });

    const macdLine = macdChart.addSeries(LineSeries, {
      color: MACD_LINE_COLOR,
      lineWidth: 1,
    });
    macdLine.setData(toLineData(props.macdLine));

    const macdSignal = macdChart.addSeries(LineSeries, {
      color: MACD_SIGNAL_COLOR,
      lineWidth: 1,
    });
    macdSignal.setData(toLineData(props.macdSignal));

    const macdHist = macdChart.addSeries(HistogramSeries, {
      base: 0,
      color: MACD_LINE_COLOR,
    });
    macdHist.setData(
      props.macdHist.map((p) => ({
        time: p.date as Time,
        value: p.value,
        color: p.value >= 0 ? UP : DOWN,
      })),
    );

    syncTimeScale([priceChart, rsiChart, macdChart]);

    const handleResize = () => {
      if (priceRef.current) priceChart.resize(priceRef.current.clientWidth, 360);
      if (rsiRef.current) rsiChart.resize(rsiRef.current.clientWidth, 140);
      if (macdRef.current) macdChart.resize(macdRef.current.clientWidth, 160);
    };
    window.addEventListener("resize", handleResize);

    priceChart.timeScale().fitContent();
    rsiChart.timeScale().fitContent();
    macdChart.timeScale().fitContent();

    return () => {
      window.removeEventListener("resize", handleResize);
      priceChart.remove();
      rsiChart.remove();
      macdChart.remove();
    };
  }, [props]);

  return (
    <div className="flex flex-col gap-2">
      <div>
        <Header title="Harga + MA overlay" legend={legendItemsForMA(props.maSeries)} />
        <div ref={priceRef} className="rounded-md border border-muted/20 bg-white/[0.02]" />
      </div>
      <div>
        <Header title="RSI 14" legend={[{ color: RSI_COLOR, label: "RSI" }]} />
        <div ref={rsiRef} className="rounded-md border border-muted/20 bg-white/[0.02]" />
      </div>
      <div>
        <Header
          title="MACD (12/26/9)"
          legend={[
            { color: MACD_LINE_COLOR, label: "line" },
            { color: MACD_SIGNAL_COLOR, label: "signal" },
            { color: UP, label: "hist +" },
            { color: DOWN, label: "hist −" },
          ]}
        />
        <div ref={macdRef} className="rounded-md border border-muted/20 bg-white/[0.02]" />
      </div>
    </div>
  );
}

interface LegendItem {
  color: string;
  label: string;
}

interface HeaderProps {
  title: string;
  legend: LegendItem[];
}

function Header({ title, legend }: HeaderProps): React.ReactElement {
  return (
    <div className="mb-1 flex items-baseline justify-between gap-3 px-1 text-xs text-muted">
      <span className="font-medium">{title}</span>
      <span className="flex flex-wrap items-center gap-3">
        {legend.map((item) => (
          <span key={item.label} className="flex items-center gap-1">
            <span
              className="inline-block h-2 w-2 rounded-sm"
              style={{ backgroundColor: item.color }}
            />
            {item.label}
          </span>
        ))}
      </span>
    </div>
  );
}

function legendItemsForMA(
  maSeries: Partial<Record<string, IndicatorSeriesPoint[]>>,
): LegendItem[] {
  return Object.entries(MA_COLORS)
    .filter(([key]) => (maSeries[key]?.length ?? 0) > 0)
    .map(([key, color]) => ({ color, label: key.replace("ma_", "MA ") }));
}

function baseOptions(width: number, height: number) {
  return {
    width,
    height,
    layout: {
      background: { type: ColorType.Solid, color: CHART_BG },
      textColor: CHART_FG,
      fontFamily: "ui-sans-serif, system-ui, Inter, sans-serif",
    },
    grid: {
      vertLines: { color: CHART_GRID },
      horzLines: { color: CHART_GRID },
    },
    rightPriceScale: { borderColor: CHART_GRID },
    timeScale: { borderColor: CHART_GRID, timeVisible: false },
    crosshair: { mode: 1 as const },
  };
}

function toCandleData(rows: OhlcvRow[]) {
  return rows
    .filter(
      (r): r is OhlcvRow & {
        open: number;
        high: number;
        low: number;
        close: number;
      } =>
        r.open != null && r.high != null && r.low != null && r.close != null,
    )
    .map((r) => ({
      time: r.date as Time,
      open: r.open,
      high: r.high,
      low: r.low,
      close: r.close,
    }));
}

function toLineData(points: IndicatorSeriesPoint[]) {
  return points.map((p) => ({ time: p.date as Time, value: p.value }));
}

function syncTimeScale(charts: IChartApi[]): void {
  for (const c of charts) {
    c.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (!range) return;
      for (const other of charts) {
        if (other === c) continue;
        other.timeScale().setVisibleLogicalRange(range);
      }
    });
  }
}
