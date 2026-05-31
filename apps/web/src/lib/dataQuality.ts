import { runPython } from "./pythonRunner";

export type FreshnessState = "fresh" | "delayed" | "stale" | "failed" | "partial" | "unknown";
export type ProviderTrustTier = "tier_1" | "tier_2" | "tier_3" | "tier_4";
export type SourceType = "ohlcv" | "fundamental" | "news" | "delivery" | "manual" | "other";

export interface ProviderHealthSnapshot {
  provider_name: string;
  provider_trust_tier: ProviderTrustTier;
  source_type: SourceType;
  freshness_state: FreshnessState;
  updated_at: string;
  last_success_at: string | null;
  last_failure_at: string | null;
  last_failure_reason: string | null;
  consecutive_failure_count: number;
  coverage_count: number | null;
  supports_dependent_flows: boolean;
  requires_caveat: boolean;
  has_visible_failure: boolean;
}

export interface DataQualityOverview {
  providers: ProviderHealthSnapshot[];
  provider_count: number;
  failed_provider_count: number;
  stale_provider_count: number;
  restricted_provider_count: number;
  total_coverage_count: number;
}

export async function fetchDataQualityOverview(): Promise<DataQualityOverview> {
  const { data } = await runPython<DataQualityOverview>("scripts.provider_health", {
    args: ["--json", "list"],
  });
  return data;
}
