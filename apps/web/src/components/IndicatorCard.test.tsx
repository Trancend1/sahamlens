import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { IndicatorCard } from "./IndicatorCard";

describe("IndicatorCard", () => {
  it("renders label, formatted value, and all explanation blocks", () => {
    const html = renderToStaticMarkup(<IndicatorCard indicator="rsi_14" value={65.5} />);

    expect(html).toContain("RSI 14");
    expect(html).toContain("65");
    expect(html).toContain("What it measures");
    expect(html).toContain("Interpretation");
    expect(html).toContain("Common false read");
    expect(html).toContain("Time horizon");
  });

  it("renders n/a placeholder when value is null", () => {
    const html = renderToStaticMarkup(<IndicatorCard indicator="ma_50" value={null} />);

    expect(html).toContain("MA 50");
    expect(html).toContain("n/a");
    expect(html).toContain("No value yet");
  });

  it("passes current price into interpretation for MA", () => {
    const html = renderToStaticMarkup(
      <IndicatorCard indicator="ma_50" value={5000} currentPrice={5500} />,
    );

    expect(html).toContain("di atas");
    expect(html).toContain("MA 50");
  });

  it("renders category badge for trend, momentum, and volume", () => {
    expect(renderToStaticMarkup(<IndicatorCard indicator="ma_5" value={100} />)).toContain(
      "trend",
    );
    expect(renderToStaticMarkup(<IndicatorCard indicator="rsi_14" value={50} />)).toContain(
      "momentum",
    );
    expect(renderToStaticMarkup(<IndicatorCard indicator="vol_avg_20" value={1e6} />)).toContain(
      "volume",
    );
  });

  it("sets data-indicator attribute for css and test hooks", () => {
    const html = renderToStaticMarkup(<IndicatorCard indicator="macd_hist" value={0.5} />);
    expect(html).toContain('data-indicator="macd_hist"');
  });
});
