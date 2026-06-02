import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { ScreenerRun } from "@/lib/screener";
import { ScreenerDashboard } from "./ScreenerDashboard";

const run: ScreenerRun = {
  run_id: "run-1",
  rule: {
    rule_id: "fundamentals-basic",
    name: "Fundamental completeness filter",
    description: "Filters symbols with visible coverage and fundamental fields.",
    required_fields: ["market_cap", "roe"],
    required_source_types: ["ohlcv", "fundamental"],
    min_coverage_tier: "tier_b",
    allowed_freshness_states: ["fresh", "delayed"],
    min_fundamental_completeness: "partial",
    min_confidence_level: "medium",
  },
  universe_count: 2,
  included_count: 1,
  excluded_count: 1,
  results: [
    {
      run_id: "run-1",
      symbol: "BBCA.JK",
      result_status: "included",
      coverage_tier: "tier_a",
      lifecycle_status: "active",
      freshness_state: "fresh",
      completeness_state: "partial",
      confidence_level: "medium",
      matched_conditions: ["market_cap exists", "roe exists"],
      failed_conditions: [],
      missing_fields: [],
      exclusion_reasons: [],
      caveats: ["Missing fields: pe_ratio, pbv."],
      explanation: "BBCA.JK matched filter Fundamental completeness filter.",
      evaluated_at: "2026-06-01T10:00:00Z",
    },
    {
      run_id: "run-1",
      symbol: "TLKM.JK",
      result_status: "excluded",
      coverage_tier: "tier_c",
      lifecycle_status: "active",
      freshness_state: "unknown",
      completeness_state: "sparse",
      confidence_level: "low",
      matched_conditions: ["market_cap exists"],
      failed_conditions: ["roe exists"],
      missing_fields: ["roe"],
      exclusion_reasons: ["coverage tier tier_c below rule minimum tier_b"],
      caveats: [],
      explanation: "TLKM.JK excluded from filter Fundamental completeness filter.",
      evaluated_at: "2026-06-01T10:00:00Z",
    },
  ],
};

describe("ScreenerDashboard", () => {
  it("renders rule summary, included rows, and exclusion reasons", () => {
    const html = renderToStaticMarkup(<ScreenerDashboard run={run} error={null} />);

    expect(html).toContain("Fundamental completeness filter");
    expect(html).toContain("BBCA.JK");
    expect(html).toContain("Included");
    expect(html).toContain("TLKM.JK");
    expect(html).toContain("Excluded");
    expect(html).toContain("coverage tier tier_c below rule minimum tier_b");
    expect(html).toContain("Confidence Medium");
  });

  it("renders empty state without hiding the local CLI path", () => {
    const html = renderToStaticMarkup(
      <ScreenerDashboard
        run={{ ...run, universe_count: 0, included_count: 0, excluded_count: 0, results: [] }}
        error={null}
      />,
    );

    expect(html).toContain("No screener rows yet.");
    expect(html).toContain("scripts.screener");
  });

  it("renders error state when the CLI cannot read local data", () => {
    const html = renderToStaticMarkup(<ScreenerDashboard run={null} error="missing table" />);

    expect(html).toContain("Gagal membaca screener.");
    expect(html).toContain("missing table");
  });
});
