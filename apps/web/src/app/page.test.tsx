import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import HomePage from "./page";

describe("HomePage", () => {
  it("renders clear navigation for the main V1 pages", () => {
    const html = renderToStaticMarkup(<HomePage />);

    for (const label of [
      "Data Quality",
      "Screener",
      "Weekly Review",
      "Strategy Rules",
      "Watchlist",
      "Trade Journal",
      "Portfolio",
    ]) {
      expect(html).toContain(label);
    }

    expect(html).toContain("Check data readiness");
    expect(html).not.toContain("profitable");
    expect(html).not.toContain("buy now");
  });
});
