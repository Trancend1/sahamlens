import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { FreshnessBadge } from "./FreshnessBadge";

describe("FreshnessBadge", () => {
  it("renders tier attribute + iso title", () => {
    const recent = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    const html = renderToStaticMarkup(<FreshnessBadge iso={recent} />);
    expect(html).toContain('data-tier="fresh"');
    expect(html).toContain(`title="${recent}"`);
  });

  it("marks old when timestamp > 72h", () => {
    const oldIso = new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString();
    const html = renderToStaticMarkup(<FreshnessBadge iso={oldIso} />);
    expect(html).toContain('data-tier="old"');
  });
});
