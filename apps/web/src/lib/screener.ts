import { runPython } from "./pythonRunner";

export type CoverageTier = "tier_a" | "tier_b" | "tier_c";
export type LifecycleStatus = "active" | "suspended" | "delisted" | "renamed" | "unknown";
export type FreshnessState = "fresh" | "delayed" | "stale" | "failed" | "partial" | "unknown";
export type CompletenessState = "complete" | "partial" | "sparse" | "missing";
export type ConfidenceLevel = "high" | "medium" | "low" | "none";
export type ScreenerResultStatus = "included" | "excluded";

export interface ScreenerRule {
  rule_id: string;
  name: string;
  description: string;
  required_fields: string[];
  required_source_types: string[];
  min_coverage_tier: CoverageTier;
  allowed_freshness_states: FreshnessState[];
  min_fundamental_completeness: CompletenessState | null;
  min_confidence_level: ConfidenceLevel | null;
}

export interface ScreenerResult {
  run_id: string;
  symbol: string;
  result_status: ScreenerResultStatus;
  coverage_tier: CoverageTier;
  lifecycle_status: LifecycleStatus;
  freshness_state: FreshnessState;
  completeness_state: CompletenessState | null;
  confidence_level: ConfidenceLevel | null;
  matched_conditions: string[];
  failed_conditions: string[];
  missing_fields: string[];
  exclusion_reasons: string[];
  caveats: string[];
  explanation: string;
  evaluated_at: string;
}

export interface ScreenerRun {
  run_id: string;
  rule: ScreenerRule;
  universe_count: number;
  included_count: number;
  excluded_count: number;
  results: ScreenerResult[];
}

interface FetchScreenerRunOptions {
  symbols?: string[];
}

export async function fetchScreenerRun(options: FetchScreenerRunOptions = {}): Promise<ScreenerRun> {
  const args = ["--json", "run", "--builtin", "fundamentals-basic", "--no-persist"];
  if (options.symbols && options.symbols.length > 0) {
    args.push("--symbols", options.symbols.join(","));
  } else {
    args.push("--from-watchlist");
  }
  const { data } = await runPython<ScreenerRun>("scripts.screener", {
    args,
    timeoutMs: 30_000,
  });
  return data;
}
