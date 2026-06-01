import { runPython } from "./pythonRunner";

export type LifecycleStatus = "active" | "suspended" | "delisted" | "renamed" | "unknown";
export type CoverageTier = "tier_a" | "tier_b" | "tier_c";
export type CompletenessState = "complete" | "partial" | "sparse" | "missing";
export type ConfidenceLevel = "high" | "medium" | "low" | "none";

export interface TickerCoverage {
  symbol: string;
  lifecycle_status: LifecycleStatus;
  coverage_tier: CoverageTier;
  lifecycle_source: string;
  coverage_source: string;
  last_verified_at: string;
  renamed_from: string | null;
  renamed_to: string | null;
  missing_data_reason: string | null;
  screener_eligible: boolean;
  alert_eligible: boolean;
  ai_explanation_eligible: boolean;
  eligibility_reason: string | null;
  updated_at: string;
}

export interface FundamentalSnapshot {
  symbol: string;
  period: string;
  statement_date: string | null;
  source: string;
  source_type: "manual" | "official" | "public_provider" | "other";
  fetched_at: string;
  imported_at: string;
  data_fields: Record<string, unknown>;
  available_fields: string[];
  missing_fields: string[];
  completeness_state: CompletenessState;
  confidence_level: ConfidenceLevel;
  confidence_score: number;
  caveat: string | null;
  reason: string | null;
}

export interface FundamentalSnapshotOverview {
  symbol: string;
  coverage: TickerCoverage | null;
  fundamental: FundamentalSnapshot | null;
  source_coverage: unknown[];
}

export async function fetchFundamentalSnapshot(symbol: string): Promise<FundamentalSnapshotOverview> {
  const { data } = await runPython<FundamentalSnapshotOverview>("scripts.fundamentals", {
    args: ["--json", "snapshot", "--symbol", symbol],
    timeoutMs: 30_000,
  });
  return data;
}
