/**
 * Static 5-block content per indicator key (per PRD §9.2).
 * Blocks: label · what it measures · current value (dynamic) · interpretation (dynamic) · common false signal · time-horizon note.
 *
 * Indicator keys mirror packages/core/indicators/engine.py INDICATOR_KEYS exactly.
 */

export type IndicatorKey =
  | "ma_5"
  | "ma_10"
  | "ma_15"
  | "ma_50"
  | "ma_200"
  | "vol_avg_20"
  | "rsi_14"
  | "macd_line"
  | "macd_signal"
  | "macd_hist";

export type IndicatorCategory = "trend" | "momentum" | "volume";

export interface InterpretContext {
  price: number | null;
}

export interface IndicatorMeta {
  label: string;
  category: IndicatorCategory;
  whatItMeasures: string;
  falseSignal: string;
  horizonNote: string;
  formatValue: (value: number) => string;
  interpret: (value: number, ctx: InterpretContext) => string;
}

const formatRupiah = (v: number): string =>
  new Intl.NumberFormat("id-ID", { maximumFractionDigits: 0 }).format(Math.round(v));

const formatVolume = (v: number): string => {
  if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(2)} M`;
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(2)} jt`;
  return new Intl.NumberFormat("id-ID", { maximumFractionDigits: 0 }).format(Math.round(v));
};

const formatDecimal = (v: number, digits = 2): string =>
  v.toLocaleString("id-ID", { minimumFractionDigits: digits, maximumFractionDigits: digits });

function priceVsLevel(value: number, ctx: InterpretContext, levelLabel: string): string {
  if (ctx.price == null) return `Level ${levelLabel}; bandingkan dengan harga sekarang.`;
  const diffPct = ((ctx.price - value) / value) * 100;
  const above = diffPct >= 0;
  const sign = above ? "di atas" : "di bawah";
  return `Harga ${sign} ${levelLabel} sekitar ${Math.abs(diffPct).toFixed(1)}%. ${
    above
      ? `Bias jangka pendek searah dengan ${levelLabel}; perhatikan reaksi saat harga retest level.`
      : `Tekanan turun terhadap ${levelLabel}; perhatikan apakah harga mampu reclaim level.`
  }`;
}

function rsiInterpret(value: number): string {
  if (value >= 70) return `RSI ${formatDecimal(value)} ≥ 70: momentum panas, berpotensi extended.`;
  if (value <= 30) return `RSI ${formatDecimal(value)} ≤ 30: momentum lemah, berpotensi oversold.`;
  if (value >= 50) return `RSI ${formatDecimal(value)} di atas 50: bias momentum positif.`;
  return `RSI ${formatDecimal(value)} di bawah 50: bias momentum negatif.`;
}

function macdHistInterpret(value: number): string {
  if (value > 0) return `Histogram positif (${formatDecimal(value, 3)}): momentum tren naik dominan.`;
  if (value < 0) return `Histogram negatif (${formatDecimal(value, 3)}): momentum tren turun dominan.`;
  return "Histogram nol: momentum netral, perhatikan arah berikutnya.";
}

function macdLineInterpret(value: number): string {
  if (value > 0) return `MACD line ${formatDecimal(value, 3)} > 0: EMA cepat di atas EMA lambat (bias naik).`;
  if (value < 0) return `MACD line ${formatDecimal(value, 3)} < 0: EMA cepat di bawah EMA lambat (bias turun).`;
  return "MACD line di nol: titik netral, perhatikan crossing berikutnya.";
}

const macdSignalInterpret = (value: number): string =>
  `Signal line ${formatDecimal(value, 3)} — banding ke MACD line untuk lihat crossing dan jarak.`;

const volumeAvgInterpret = (value: number): string =>
  `Average volume 20 hari: ${formatVolume(value)}. Bandingkan volume hari ini terhadap baseline ini.`;

export const INDICATOR_META: Record<IndicatorKey, IndicatorMeta> = {
  ma_5: {
    label: "MA 5",
    category: "trend",
    whatItMeasures:
      "Rata-rata harga close 5 hari terakhir — proxy bias jangka sangat pendek.",
    falseSignal:
      "Sering whipsaw di sideways. Crossing terhadap harga bisa false setiap beberapa hari.",
    horizonNote:
      "Relevan untuk swing 1–3 hari. Tidak relevan untuk position trade berbulan.",
    formatValue: (v) => formatRupiah(v),
    interpret: (v, ctx) => priceVsLevel(v, ctx, "MA 5"),
  },
  ma_10: {
    label: "MA 10",
    category: "trend",
    whatItMeasures: "Rata-rata close 10 hari — bias jangka pendek (≈ 2 minggu trading).",
    falseSignal: "Masih sensitif terhadap noise harian; konfirmasi dengan MA lebih panjang.",
    horizonNote: "Cocok dipakai bersama MA 50 untuk swing 1–4 minggu.",
    formatValue: (v) => formatRupiah(v),
    interpret: (v, ctx) => priceVsLevel(v, ctx, "MA 10"),
  },
  ma_15: {
    label: "MA 15",
    category: "trend",
    whatItMeasures: "Rata-rata close 15 hari — referensi short–mid yang umum di IDX.",
    falseSignal: "Dekat MA 10/20, jangan double-counting interpretasi.",
    horizonNote: "Berguna untuk swing 2–6 minggu.",
    formatValue: (v) => formatRupiah(v),
    interpret: (v, ctx) => priceVsLevel(v, ctx, "MA 15"),
  },
  ma_50: {
    label: "MA 50",
    category: "trend",
    whatItMeasures: "Rata-rata close 50 hari — tren menengah; pivot umum untuk swing trader.",
    falseSignal: "Saat range, harga sering crossing tanpa arah jelas. Konfirmasi dengan struktur HH/LL.",
    horizonNote: "Cocok untuk holding period 1–3 bulan.",
    formatValue: (v) => formatRupiah(v),
    interpret: (v, ctx) => priceVsLevel(v, ctx, "MA 50"),
  },
  ma_200: {
    label: "MA 200",
    category: "trend",
    whatItMeasures: "Rata-rata close 200 hari — tren struktural jangka panjang.",
    falseSignal: "Crossing MA 200 di pasar choppy bukan sinyal tunggal; pakai dengan volume + struktur.",
    horizonNote: "Relevan untuk position trade 3 bulan – 1 tahun+.",
    formatValue: (v) => formatRupiah(v),
    interpret: (v, ctx) => priceVsLevel(v, ctx, "MA 200"),
  },
  vol_avg_20: {
    label: "Volume avg 20",
    category: "volume",
    whatItMeasures:
      "Rata-rata volume 20 hari — baseline partisipasi. Bukan sinyal arah, hanya konfirmasi.",
    falseSignal:
      "Volume spike saat earnings / corporate action bukan sinyal teknikal; verifikasi katalis dulu.",
    horizonNote:
      "Berguna semua horizon; lihat rasio volume hari ini vs baseline (>2× = perlu investigasi).",
    formatValue: (v) => formatVolume(v),
    interpret: (v) => volumeAvgInterpret(v),
  },
  rsi_14: {
    label: "RSI 14",
    category: "momentum",
    whatItMeasures:
      "Momentum harga (skala 0–100). > 70 secara konvensional overbought, < 30 oversold.",
    falseSignal:
      "Di tren kuat, RSI bisa stay > 70 / < 30 berhari-hari. Overbought ≠ harus jual.",
    horizonNote: "Periode 14 cocok untuk swing trading mingguan.",
    formatValue: (v) => formatDecimal(v),
    interpret: (v) => rsiInterpret(v),
  },
  macd_line: {
    label: "MACD line (12-26)",
    category: "momentum",
    whatItMeasures: "Selisih EMA 12 dan EMA 26 — momentum tren.",
    falseSignal:
      "Crossing dekat nol di sideways sering false. Konfirmasi dengan histogram & harga.",
    horizonNote: "Pakai untuk konfirmasi tren swing 2–8 minggu, bukan timing presisi.",
    formatValue: (v) => formatDecimal(v, 3),
    interpret: (v) => macdLineInterpret(v),
  },
  macd_signal: {
    label: "MACD signal (9 EMA)",
    category: "momentum",
    whatItMeasures: "EMA 9-period dari MACD line — referensi crossing.",
    falseSignal: "Crossing tunggal tidak cukup; cek histogram + struktur harga.",
    horizonNote: "Selalu baca berpasangan dengan MACD line; standalone kurang berarti.",
    formatValue: (v) => formatDecimal(v, 3),
    interpret: (v) => macdSignalInterpret(v),
  },
  macd_hist: {
    label: "MACD histogram",
    category: "momentum",
    whatItMeasures: "Selisih MACD line dan signal — visual momentum delta.",
    falseSignal:
      "Histogram kecil di sekitar nol sering noise. Cari ekspansi/kontraksi konsisten beberapa bar.",
    horizonNote: "Bagus untuk early momentum shift; tetap konfirmasi dengan struktur harga.",
    formatValue: (v) => formatDecimal(v, 3),
    interpret: (v) => macdHistInterpret(v),
  },
};

export const INDICATOR_KEYS: readonly IndicatorKey[] = [
  "ma_5",
  "ma_10",
  "ma_15",
  "ma_50",
  "ma_200",
  "vol_avg_20",
  "rsi_14",
  "macd_line",
  "macd_signal",
  "macd_hist",
];
