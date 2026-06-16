import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { FundamentalSnapshotOverview } from "@/lib/fundamentals";
import { FundamentalSnapshotCard } from "./FundamentalSnapshotCard";

function overview(completeness: "complete" | "partial"): FundamentalSnapshotOverview {
  return {
    symbol: "BBCA.JK",
    coverage: {
      symbol: "BBCA.JK",
      lifecycle_status: "active",
      coverage_tier: completeness === "complete" ? "tier_a" : "tier_b",
      lifecycle_source: "manual",
      coverage_source: "manual",
      last_verified_at: "2026-06-01T09:00:00Z",
      renamed_from: null,
      renamed_to: null,
      missing_data_reason: completeness === "complete" ? null : "fundamental completeness is partial",
      screener_eligible: true,
      alert_eligible: true,
      ai_explanation_eligible: true,
      eligibility_reason: "full support with visible caveats",
      updated_at: "2026-06-01T09:00:00Z",
    },
    fundamental: {
      symbol: "BBCA.JK",
      period: "2026Q1",
      statement_date: null,
      source: "manual",
      source_type: "manual",
      fetched_at: "2026-06-01T09:00:00Z",
      imported_at: "2026-06-01T09:00:00Z",
      data_fields: { market_cap: 1000, roe: 0.18 },
      available_fields: ["market_cap", "roe"],
      missing_fields: completeness === "complete" ? [] : ["pe_ratio", "pbv"],
      completeness_state: completeness,
      confidence_level: completeness === "complete" ? "high" : "medium",
      confidence_score: completeness === "complete" ? 0.9 : 0.6,
      caveat: completeness === "complete" ? null : "Missing fields: pe_ratio, pbv.",
      reason: `completeness=${completeness}`,
    },
    source_coverage: [],
  };
}

describe("FundamentalSnapshotCard", () => {
  it("renders coverage, lifecycle, completeness, and confidence badges", () => {
    const html = renderToStaticMarkup(<FundamentalSnapshotCard overview={overview("complete")} />);

    expect(html).toContain("Tier A");
    expect(html).toContain("Active");
    expect(html).toContain("Complete");
    expect(html).toContain("Confidence High");
  });

  it("renders read-only caveats when fields are missing", () => {
    const html = renderToStaticMarkup(<FundamentalSnapshotCard overview={overview("partial")} />);

    expect(html).toContain("Read-only");
    expect(html).toContain("Missing fields: pe_ratio, pbv");
    expect(html).toContain("Missing: pe_ratio, pbv");
  });

  it("renders missing state with webui action hint", () => {
    const html = renderToStaticMarkup(
      <FundamentalSnapshotCard
        overview={{
          symbol: "TLKM.JK",
          coverage: null,
          fundamental: null,
          source_coverage: [],
        }}
      />,
    );

    expect(html).toContain("Coverage unknown");
    expect(html).toContain("Fundamental missing");
    expect(html).toContain("Refresh fundamentals from the stock detail page");
  });
});
