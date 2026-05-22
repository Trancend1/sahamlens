import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { StockFreshnessBar } from "./StockFreshnessBar";

describe("StockFreshnessBar", () => {
  it("renders nothing when lastDate is null", () => {
    const html = renderToStaticMarkup(<StockFreshnessBar lastDate={null} />);
    expect(html).toBe("");
  });

  it("renders nothing when lastDate is undefined", () => {
    const html = renderToStaticMarkup(<StockFreshnessBar lastDate={undefined} />);
    expect(html).toBe("");
  });

  it("renders date text when lastDate provided", () => {
    const html = renderToStaticMarkup(<StockFreshnessBar lastDate="2026-05-20" />);
    expect(html).toContain("2026-05-20");
    expect(html).toContain("Data per");
  });

  it("renders FreshnessBadge when lastDate provided", () => {
    const html = renderToStaticMarkup(<StockFreshnessBar lastDate="2026-05-20" />);
    // FreshnessBadge sets data-tier
    expect(html).toContain("data-tier");
  });
});
