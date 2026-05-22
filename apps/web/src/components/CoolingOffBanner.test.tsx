import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { CoolingOffBanner } from "./CoolingOffBanner";

describe("CoolingOffBanner", () => {
  it("renders null when no trigger (calm + green)", () => {
    const html = renderToStaticMarkup(
      <CoolingOffBanner emotion="calm" riskFlag="green" />,
    );
    expect(html).toBe("");
  });

  it("renders null when both null", () => {
    const html = renderToStaticMarkup(
      <CoolingOffBanner emotion={null} riskFlag={null} />,
    );
    expect(html).toBe("");
  });

  it("renders null for uncertain emotion with non-red flag", () => {
    const html = renderToStaticMarkup(
      <CoolingOffBanner emotion="uncertain" riskFlag="amber" />,
    );
    expect(html).toBe("");
  });

  it("renders banner for greedy emotion", () => {
    const html = renderToStaticMarkup(
      <CoolingOffBanner emotion="greedy" riskFlag="green" />,
    );
    expect(html).toContain("cooling-off");
    expect(html).toContain("greedy");
  });

  it("renders banner for fearful emotion", () => {
    const html = renderToStaticMarkup(
      <CoolingOffBanner emotion="fearful" riskFlag="amber" />,
    );
    expect(html).toContain("cooling-off");
  });

  it("renders banner for excited emotion", () => {
    const html = renderToStaticMarkup(
      <CoolingOffBanner emotion="excited" riskFlag="green" />,
    );
    expect(html).toContain("cooling-off");
  });

  it("renders banner for red risk flag even with calm emotion", () => {
    const html = renderToStaticMarkup(
      <CoolingOffBanner emotion="calm" riskFlag="red" />,
    );
    expect(html).toContain("cooling-off");
    expect(html).toContain("Red");
  });

  it("renders both tags when emotion + red", () => {
    const html = renderToStaticMarkup(
      <CoolingOffBanner emotion="greedy" riskFlag="red" />,
    );
    expect(html).toContain("greedy");
    expect(html).toContain("Red");
  });

  it("has role=alert for accessibility", () => {
    const html = renderToStaticMarkup(
      <CoolingOffBanner emotion="greedy" riskFlag="green" />,
    );
    expect(html).toContain('role="alert"');
  });

  it("shows 24 jam message", () => {
    const html = renderToStaticMarkup(
      <CoolingOffBanner emotion="greedy" riskFlag="green" />,
    );
    expect(html).toContain("24 jam");
  });
});
