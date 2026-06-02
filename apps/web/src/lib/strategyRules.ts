import { runPython } from "./pythonRunner";
import type { StrategyRuleEvaluation } from "./journalReview";

export type StrategyRuleCategory =
  | "journal_completeness"
  | "risk_discipline"
  | "plan_adherence"
  | "emotion_discipline"
  | "review_hygiene";
export type NeedsDataBehavior = "needs_data" | "skip";

export interface StrategyRule {
  rule_id: string;
  name: string;
  description: string;
  rule_category: StrategyRuleCategory;
  required_fields: string[];
  violation_code: string;
  needs_data_behavior: NeedsDataBehavior;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type { StrategyRuleEvaluation };

interface FetchStrategyRuleResultsOptions {
  reviewId?: string;
}

export async function fetchStrategyRules(): Promise<StrategyRule[]> {
  const { data } = await runPython<StrategyRule[]>("scripts.journal_review", {
    args: ["--json", "rules", "list", "--active-only"],
    timeoutMs: 30_000,
  });
  return data;
}

export async function fetchStrategyRuleResults(
  options: FetchStrategyRuleResultsOptions = {},
): Promise<StrategyRuleEvaluation[]> {
  const args = ["--json", "rules", "results"];
  if (options.reviewId) args.push("--review-id", options.reviewId);
  const { data } = await runPython<StrategyRuleEvaluation[]>("scripts.journal_review", {
    args,
    timeoutMs: 30_000,
  });
  return data;
}
