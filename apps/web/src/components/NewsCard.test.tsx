import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { NewsRecent } from "@/lib/stockDetail";
import { NewsCard } from "./NewsCard";

const base: NewsRecent = {
  news_id: 1,
  url: "https://finance.detik.com/news/42",
  summary: "BBCA naikkan target kredit tahun ini.",
  affected_tickers: ["BBCA.JK"],
  sentiment_label: "bullish",
  caveats: [],
  source_quality: "reputable_media",
  confidence: 0.85,
  summarized_at: new Date().toISOString(),
};

describe("NewsCard", () => {
  it("renders summary + sentiment + ticker", () => {
    const html = renderToStaticMarkup(<NewsCard news={base} />);
    expect(html).toContain("BBCA naikkan target kredit");
    expect(html).toContain('data-sentiment="bullish"');
    expect(html).toContain("BBCA.JK");
    expect(html).toContain("Media kredibel");
  });

  it("shows low-confidence banner when confidence < 0.6", () => {
    const html = renderToStaticMarkup(
      <NewsCard news={{ ...base, confidence: 0.45, caveats: ["sumber tunggal"] }} />,
    );
    expect(html).toContain("Confidence rendah");
    expect(html).toContain("sumber tunggal");
  });

  it("hides caveats block when caveats empty", () => {
    const html = renderToStaticMarkup(<NewsCard news={base} />);
    expect(html).not.toContain("Caveat");
  });

  it("renders host hyperlink from url", () => {
    const html = renderToStaticMarkup(<NewsCard news={base} />);
    expect(html).toContain("finance.detik.com");
    expect(html).toContain('rel="noopener noreferrer"');
  });

  it("renders different colors per sentiment", () => {
    const bear = renderToStaticMarkup(
      <NewsCard news={{ ...base, sentiment_label: "bearish" }} />,
    );
    expect(bear).toContain("Bearish");
    const mixed = renderToStaticMarkup(
      <NewsCard news={{ ...base, sentiment_label: "mixed" }} />,
    );
    expect(mixed).toContain("Mixed");
  });
});
