import { describe, it, expect, beforeAll } from "vitest";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { CLI_COMMANDS, OPERATION_CLI_MAP, runCli, type CliCommandKey } from "@/lib/cliCommands";
import { OPERATIONS } from "@/lib/operations";

const execFileAsync = promisify(execFile);

/** True if Python + duckdb are available (CI web job skips Python setup). */
let pythonReady = false;

beforeAll(async () => {
  try {
    await execFileAsync("python", ["-c", "import duckdb"], { timeout: 10_000 });
    pythonReady = true;
  } catch {
    pythonReady = false;
  }
});

/**
 * Contract tests for the CLI adapter.
 *
 * The first block is a fast unit check that every command obeys the global
 * `--json`-before-subcommand rule and uses correct argparse subcommand names.
 * The second block actually spawns a read-only Python CLI to prove the contract
 * holds end-to-end (no mocks).
 */

describe("CLI command contracts (static)", () => {
  it("places --json as the first argument for every command", () => {
    for (const [key, spec] of Object.entries(CLI_COMMANDS)) {
      const args = spec.buildArgs({ symbol: "BBCA", fromWatchlist: true, days: 7 });
      expect(args[0], `${key} must emit --json first`).toBe("--json");
    }
  });

  it("uses the real argparse subcommand names (no legacy mistakes)", () => {
    const fundamentals = CLI_COMMANDS["fundamentals.refresh"].buildArgs({ symbol: "BBCA" });
    expect(fundamentals).toContain("refresh-coverage");
    expect(fundamentals).not.toContain("coverage");

    const providerHealth = CLI_COMMANDS["provider_health.refresh"].buildArgs({});
    expect(providerHealth).toContain("refresh-yfinance");

    const news = CLI_COMMANDS["news.ingest"].buildArgs({});
    expect(news).not.toContain("--symbols");
    expect(news).not.toContain("--from-watchlist");
  });

  it("supplies required --start/--end for journal_review commands", () => {
    for (const key of ["strategy_rules.evaluate", "weekly_review.generate"] as const) {
      const args = CLI_COMMANDS[key].buildArgs({});
      expect(args).toContain("--start");
      expect(args).toContain("--end");
    }
  });

  it("maps every operations-registry id to a known CLI command", () => {
    for (const op of OPERATIONS) {
      const key = OPERATION_CLI_MAP[op.id] as CliCommandKey | undefined;
      expect(key, `operation ${op.id} must map to a CLI command`).toBeDefined();
      expect(CLI_COMMANDS[key as CliCommandKey]).toBeDefined();
    }
  });
});

describe("CLI execution (real subprocess, read-only)", () => {
  it(
    "freshness.check exits 0 and returns a structured report",
    async () => {
      if (!pythonReady) return;
      const result = await runCli("freshness.check");
      expect(result.ok).toBe(true);
      expect(result.data).not.toBeNull();
      const report = result.data as { total_count: number; records: unknown[] };
      expect(typeof report.total_count).toBe("number");
      expect(Array.isArray(report.records)).toBe(true);
    },
    60_000,
  );
});

describe("operations run route (real route → real CLI, no mocks)", () => {
  it(
    "POST /api/operations/alerts/run returns HTTP 200 (not 500)",
    async () => {
      if (!pythonReady) return;
      const { POST } = await import("@/app/api/operations/[type]/run/route");
      const req = new Request("http://localhost/api/operations/alerts/run", {
        method: "POST",
      }) as unknown as import("next/server").NextRequest;

      const res = await POST(req, { params: Promise.resolve({ type: "alerts" }) });
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.ok).toBe(true);
      expect(body.type).toBe("alerts");
    },
    60_000,
  );

  it(
    "GET /api/data/freshness returns HTTP 200 with a report (StaleDataBanner source)",
    async () => {
      if (!pythonReady) return;
      const { GET } = await import("@/app/api/data/freshness/route");
      const res = await GET();
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(typeof body.total_count).toBe("number");
      expect(Array.isArray(body.records)).toBe(true);
    },
    60_000,
  );
});
