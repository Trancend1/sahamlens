import { describe, expect, it, vi } from "vitest";

vi.mock("./pythonRunner", () => ({
  runPython: vi.fn(),
}));

const { runPython } = await import("./pythonRunner");
const runMock = vi.mocked(runPython);

describe("fetchScreenerRun", () => {
  it("calls screener CLI for the built-in watchlist filter", async () => {
    runMock.mockResolvedValueOnce({
      data: {
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
        universe_count: 0,
        included_count: 0,
        excluded_count: 0,
        results: [],
      },
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchScreenerRun } = await import("./screener");

    const run = await fetchScreenerRun();

    expect(run.rule.rule_id).toBe("fundamentals-basic");
    expect(runMock).toHaveBeenCalledWith("scripts.screener", {
      args: ["--json", "run", "--builtin", "fundamentals-basic", "--from-watchlist"],
      timeoutMs: 30_000,
    });
  });

  it("can run the built-in filter for explicit symbols", async () => {
    runMock.mockResolvedValueOnce({
      data: {
        run_id: "run-1",
        rule: {
          rule_id: "fundamentals-basic",
          name: "Fundamental completeness filter",
          description: "Filters symbols with visible coverage and fundamental fields.",
          required_fields: [],
          required_source_types: [],
          min_coverage_tier: "tier_b",
          allowed_freshness_states: ["fresh", "delayed"],
          min_fundamental_completeness: null,
          min_confidence_level: null,
        },
        universe_count: 0,
        included_count: 0,
        excluded_count: 0,
        results: [],
      },
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchScreenerRun } = await import("./screener");

    await fetchScreenerRun({ symbols: ["BBCA", "TLKM"] });

    expect(runMock).toHaveBeenCalledWith("scripts.screener", {
      args: ["--json", "run", "--builtin", "fundamentals-basic", "--symbols", "BBCA,TLKM"],
      timeoutMs: 30_000,
    });
  });
});
