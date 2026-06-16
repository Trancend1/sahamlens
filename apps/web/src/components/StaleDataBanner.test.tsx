import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { StaleDataBanner } from "./StaleDataBanner";

describe("StaleDataBanner", () => {
  it("renders nothing on initial render (no report yet)", () => {
    const html = renderToStaticMarkup(<StaleDataBanner />);
    expect(html).toBe("");
  });
});
