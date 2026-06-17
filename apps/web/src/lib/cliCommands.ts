/**
 * Centralized CLI command adapter.
 *
 * Single source of truth for how the WebUI invokes Python CLIs. Every API route
 * that runs a one-shot script MUST go through `runCli` instead of building
 * arguments inline. This guarantees correct contracts:
 *
 *  - `--json` is a GLOBAL flag in most CLIs and must come BEFORE the subcommand.
 *  - Subcommand names must match argparse exactly (e.g. `refresh-coverage`,
 *    `refresh-yfinance`, not `coverage refresh` / `refresh`).
 *  - Required arguments (e.g. journal_review `--start`/`--end`) must be supplied.
 *
 * Success is determined by process exit code (via `runPythonRaw`), not by output
 * shape. JSON parsing is best-effort and never causes a false failure.
 */
import { runPythonRaw } from "./pythonRunner";

export interface CliParams {
  /** Single ticker symbol (per-stock operations). */
  symbol?: string;
  /** Use the watchlist as the symbol source instead of an explicit symbol. */
  fromWatchlist?: boolean;
  /** Price ingestion window in days. */
  days?: number;
}

export interface CliResult {
  ok: boolean;
  /** Parsed JSON payload when the CLI emitted valid JSON, otherwise null. */
  data: unknown | null;
  stdout: string;
  stderr: string;
}

interface CliSpec {
  module: string;
  buildArgs: (params: CliParams) => string[];
  timeoutMs: number;
}

/** Local-date `YYYY-MM-DD` for `n` days ago (n=0 → today). */
function isoDate(daysAgo: number): string {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString().slice(0, 10);
}

function symbolOrWatchlist(p: CliParams): string[] {
  return p.symbol ? ["--symbols", p.symbol] : ["--from-watchlist"];
}

export const CLI_COMMANDS = {
  "prices.refresh": {
    module: "scripts.ingest_prices",
    buildArgs: (p) => ["--json", ...symbolOrWatchlist(p), "--days", String(p.days ?? 365)],
    timeoutMs: 180_000,
  },
  "indicators.calculate": {
    module: "scripts.calculate_indicators",
    buildArgs: (p) => ["--json", ...symbolOrWatchlist(p)],
    timeoutMs: 60_000,
  },
  "fundamentals.refresh": {
    module: "scripts.fundamentals",
    buildArgs: (p) => ["--json", "refresh-coverage", ...symbolOrWatchlist(p)],
    timeoutMs: 180_000,
  },
  "news.ingest": {
    // ingest_news has no per-symbol concept; it ingests all configured feeds.
    module: "scripts.ingest_news",
    buildArgs: (_p) => ["--json"],
    timeoutMs: 180_000,
  },
  "news.summarize": {
    module: "scripts.summarize_news",
    buildArgs: (_p) => ["--json", "--from-watchlist"],
    timeoutMs: 120_000,
  },
  "provider_health.refresh": {
    module: "scripts.provider_health",
    // refresh-yfinance requires a symbol source; default to the watchlist.
    buildArgs: (p) => ["--json", "refresh-yfinance", ...symbolOrWatchlist(p)],
    timeoutMs: 120_000,
  },
  "screener.run": {
    module: "scripts.screener",
    buildArgs: (p) => [
      "--json",
      "run",
      "--builtin",
      "fundamentals-basic",
      ...(p.fromWatchlist ? ["--from-watchlist"] : []),
    ],
    timeoutMs: 120_000,
  },
  "alerts.evaluate": {
    module: "scripts.alerts",
    buildArgs: (_p) => ["--json", "evaluate"],
    timeoutMs: 60_000,
  },
  "strategy_rules.evaluate": {
    module: "scripts.journal_review",
    buildArgs: (_p) => ["--json", "rules", "evaluate", "--start", isoDate(7), "--end", isoDate(0)],
    timeoutMs: 60_000,
  },
  "weekly_review.generate": {
    module: "scripts.journal_review",
    buildArgs: (_p) => ["--json", "review", "generate", "--start", isoDate(7), "--end", isoDate(0)],
    timeoutMs: 120_000,
  },
  "freshness.check": {
    module: "scripts.freshness",
    buildArgs: (_p) => ["--json", "check"],
    timeoutMs: 15_000,
  },
  "freshness.refresh": {
    module: "scripts.freshness",
    buildArgs: (_p) => ["--json", "refresh"],
    timeoutMs: 300_000,
  },
} satisfies Record<string, CliSpec>;

export type CliCommandKey = keyof typeof CLI_COMMANDS;

/** Map an operations-registry id to its CLI command key. */
export const OPERATION_CLI_MAP: Record<string, CliCommandKey> = {
  provider_health: "provider_health.refresh",
  prices: "prices.refresh",
  fundamentals: "fundamentals.refresh",
  news: "news.ingest",
  alerts: "alerts.evaluate",
  screener: "screener.run",
  strategy_rules: "strategy_rules.evaluate",
  weekly_review: "weekly_review.generate",
};

/**
 * Run a CLI command by key. Throws `PythonRunnerError` on non-zero exit
 * (or spawn failure); callers translate that into an HTTP error response.
 */
export async function runCli(key: CliCommandKey, params: CliParams = {}): Promise<CliResult> {
  const spec = CLI_COMMANDS[key];
  const { stdout, stderr } = await runPythonRaw(spec.module, {
    args: spec.buildArgs(params),
    timeoutMs: spec.timeoutMs,
  });

  let data: unknown = null;
  const trimmed = stdout.trim();
  if (trimmed) {
    try {
      data = JSON.parse(trimmed);
    } catch {
      data = null; // plain-text output is acceptable; success is exit-code based
    }
  }
  return { ok: true, data, stdout, stderr };
}
