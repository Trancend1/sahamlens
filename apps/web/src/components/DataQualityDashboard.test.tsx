import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { DataQualityOverview } from "@/lib/dataQuality";
import { DataQualityDashboard } from "./DataQualityDashboard";

function overview(states: string[]): DataQualityOverview {
  return {
    provider_count: states.length,
    failed_provider_count: states.filter((state) => state === "failed").length,
    stale_provider_count: states.filter((state) => state === "stale").length,
    restricted_provider_count: states.filter((state) =>
      ["stale", "failed", "partial", "unknown"].includes(state),
    ).length,
    total_coverage_count: 10,
    providers: states.map((state, index) => ({
      provider_name: `provider-${state}`,
      provider_trust_tier: "tier_3",
      source_type: "ohlcv",
      freshness_state: state as DataQualityOverview["providers"][number]["freshness_state"],
      updated_at: "2026-05-31T09:00:00Z",
      last_success_at: state === "failed" || state === "unknown" ? null : "2026-05-31T08:00:00Z",
      last_failure_at: state === "failed" ? "2026-05-31T09:00:00Z" : null,
      last_failure_reason: state === "failed" ? "rate limited" : null,
      consecutive_failure_count: state === "failed" ? 1 : 0,
      coverage_count: index + 1,
      supports_dependent_flows: ["fresh", "delayed"].includes(state),
      requires_caveat: state !== "fresh",
      has_visible_failure: state === "failed",
    })),
  };
}

describe("DataQualityDashboard", () => {
  it("renders empty state when no providers exist", () => {
    const html = renderToStaticMarkup(
      <DataQualityDashboard
        overview={overview([])}
        error={null}
      />,
    );
    expect(html).toContain("Belum ada provider health snapshot");
  });

  it("renders all V1 freshness states", () => {
    const html = renderToStaticMarkup(
      <DataQualityDashboard
        overview={overview(["fresh", "delayed", "stale", "failed", "partial", "unknown"])}
        error={null}
      />,
    );
    for (const state of ["fresh", "delayed", "stale", "failed", "partial", "unknown"]) {
      expect(html).toContain(`data-state="${state}"`);
    }
  });

  it("renders load error without hiding dashboard context", () => {
    const html = renderToStaticMarkup(
      <DataQualityDashboard
        overview={null}
        error="boom"
      />,
    );
    expect(html).toContain("Gagal membaca data quality");
    expect(html).toContain("boom");
  });
});
