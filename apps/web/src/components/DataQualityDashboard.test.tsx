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
        runtimeStatus={null}
        runtimeError={null}
      />,
    );
    expect(html).toContain("Provider health has not been checked yet");
    expect(html).toContain("Refresh provider health");
  });

  it("renders all V1 freshness states", () => {
    const html = renderToStaticMarkup(
      <DataQualityDashboard
        overview={overview(["fresh", "delayed", "stale", "failed", "partial", "unknown"])}
        error={null}
        runtimeStatus={null}
        runtimeError={null}
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
        error={{
          code: "command_failed",
          message: "Runtime command failed.",
          details: "boom",
          recommended_command: null,
        }}
        runtimeStatus={null}
        runtimeError={null}
      />,
    );
    expect(html).toContain("Data quality could not be loaded");
    expect(html).toContain("boom");
  });

  it("renders runtime readiness with migration recovery command", () => {
    const html = renderToStaticMarkup(
      <DataQualityDashboard
        overview={overview([])}
        error={null}
        runtimeError={null}
        runtimeStatus={{
          ok: false,
          status: "stale",
          db_path: "D:/DevSpace/Projects/sahamlens/data/private/sahamlens.duckdb",
          python_executable: "python",
          applied_migrations: ["0001", "0002", "0003", "0004", "0005"],
          pending_migrations: ["0006"],
          missing_tables: ["weekly_review_runs"],
          schema_status: "stale",
          warnings: [
            {
              code: "schema_stale",
              message: "Local schema is not ready for the current V1 runtime.",
              recommended_command: "uv run python -m scripts.migrate",
            },
          ],
          errors: [
            {
              code: "missing_table",
              message: "Missing required runtime table(s): weekly_review_runs.",
              recommended_command: "uv run python -m scripts.migrate",
            },
          ],
          recommended_commands: ["uv run python -m scripts.migrate"],
        }}
      />,
    );

    expect(html).toContain("Runtime Readiness");
    expect(html).toContain("Not Ready");
    expect(html).toContain("Check runtime status");
    expect(html).toContain("weekly_review_runs");
    expect(html).toContain("scripts.migrate");
    expect(html).not.toContain("Traceback");
    expect(html).not.toContain("no such table");
  });

  it("renders runtime unavailable state for missing python executable", () => {
    const html = renderToStaticMarkup(
      <DataQualityDashboard
        overview={null}
        error={null}
        runtimeStatus={null}
        runtimeError={{
          code: "python_not_found",
          message: "Python executable was not found.",
          details: "Set PYTHON_BIN to the project virtualenv Python before starting the web app.",
          recommended_command: '$env:PYTHON_BIN=(Resolve-Path ".venv/Scripts/python.exe").Path',
        }}
      />,
    );

    expect(html).toContain("Runtime not ready");
    expect(html).toContain("Python executable was not found.");
    expect(html).toContain("PYTHON_BIN");
    expect(html).not.toContain("Traceback");
  });

  it("does not mention deferred alert workflows in V1-S5 provider copy", () => {
    const html = renderToStaticMarkup(
      <DataQualityDashboard
        overview={overview(["stale", "failed"])}
        error={null}
        runtimeStatus={null}
        runtimeError={null}
      />,
    );

    expect(html.toLowerCase()).not.toContain("alerts");
  });
});
