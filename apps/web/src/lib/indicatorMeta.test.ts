import { describe, expect, it } from "vitest";
import { INDICATOR_KEYS, INDICATOR_META, type IndicatorKey } from "./indicatorMeta";

describe("INDICATOR_META", () => {
  it("covers every INDICATOR_KEY with full 5-block content", () => {
    for (const key of INDICATOR_KEYS) {
      const meta = INDICATOR_META[key];
      expect(meta).toBeDefined();
      expect(meta.label.length).toBeGreaterThan(0);
      expect(meta.whatItMeasures.length).toBeGreaterThan(20);
      expect(meta.falseSignal.length).toBeGreaterThan(20);
      expect(meta.horizonNote.length).toBeGreaterThan(20);
      expect(typeof meta.interpret).toBe("function");
      expect(typeof meta.formatValue).toBe("function");
    }
  });

  it("formats RSI as 2-decimal", () => {
    expect(INDICATOR_META.rsi_14.formatValue(65.3456)).toMatch(/65[,.]35/);
  });

  it("interprets RSI ≥ 70 as extended", () => {
    const text = INDICATOR_META.rsi_14.interpret(72, { price: null });
    expect(text.toLowerCase()).toContain("panas");
    expect(text).toContain("extended");
  });

  it("interprets RSI ≤ 30 as oversold", () => {
    const text = INDICATOR_META.rsi_14.interpret(25, { price: null });
    expect(text.toLowerCase()).toContain("oversold");
  });

  it("MACD hist positive ≠ negative interpretation", () => {
    const pos = INDICATOR_META.macd_hist.interpret(0.5, { price: null });
    const neg = INDICATOR_META.macd_hist.interpret(-0.5, { price: null });
    expect(pos).not.toEqual(neg);
    expect(pos.toLowerCase()).toContain("naik");
    expect(neg.toLowerCase()).toContain("turun");
  });

  it("MA interpretation falls back to generic when price is null", () => {
    const text = INDICATOR_META.ma_50.interpret(5000, { price: null });
    expect(text).toContain("MA 50");
    expect(text).toContain("bandingkan");
  });

  it("MA interpretation uses price context when provided (above)", () => {
    const text = INDICATOR_META.ma_50.interpret(5000, { price: 5500 });
    expect(text).toContain("di atas");
  });

  it("MA interpretation uses price context when provided (below)", () => {
    const text = INDICATOR_META.ma_50.interpret(5000, { price: 4500 });
    expect(text).toContain("di bawah");
  });

  it("volume avg formatValue uses jt/M units for large numbers", () => {
    expect(INDICATOR_META.vol_avg_20.formatValue(15_000_000)).toContain("jt");
    expect(INDICATOR_META.vol_avg_20.formatValue(2_500_000_000)).toContain("M");
  });

  it("all keys present in INDICATOR_KEYS map to META", () => {
    const expected: IndicatorKey[] = [
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
    expect([...INDICATOR_KEYS].sort()).toEqual(expected.sort());
  });
});
