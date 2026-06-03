import { runPython, toRuntimeFetchError } from "./pythonRunner";

export type WeeklyReviewStatus = "completed" | "partial" | "failed";
export type WeeklyFindingType =
  | "behavior_pattern"
  | "rule_violation"
  | "missing_data"
  | "risk_discipline"
  | "follow_up"
  | "caveat";
export type WeeklyFindingSeverity = "info" | "warning" | "critical";
export type StrategyEvaluationStatus = "pass" | "fail" | "needs_data" | "skipped";

export interface WeeklyReviewFinding {
  finding_id: string;
  review_id: string;
  finding_type: WeeklyFindingType;
  title: string;
  detail: string;
  severity: WeeklyFindingSeverity;
  evidence: string[];
  caveats: string[];
  created_at: string;
}

export interface StrategyRuleViolation {
  violation_id: string;
  evaluation_id: string;
  review_id: string | null;
  rule_id: string;
  journal_id: number | null;
  symbol: string | null;
  violation_code: string;
  violation_detail: string;
  evidence: string[];
  caveats: string[];
  created_at: string;
}

export interface StrategyRuleEvaluation {
  evaluation_id: string;
  review_id: string | null;
  rule_id: string;
  journal_id: number | null;
  symbol: string | null;
  evaluation_status: StrategyEvaluationStatus;
  evaluated_at: string;
  evidence: string[];
  caveats: string[];
  reason: string;
  violations: StrategyRuleViolation[];
}

export interface WeeklyReviewRun {
  review_id: string;
  period_start: string;
  period_end: string;
  generated_at: string;
  status: WeeklyReviewStatus;
  journal_entry_count: number;
  reviewed_plan_count: number;
  rule_evaluation_count: number;
  violation_count: number;
  needs_data_count: number;
  summary: string;
  evidence: string[];
  caveats: string[];
  findings: WeeklyReviewFinding[];
  rule_evaluations: StrategyRuleEvaluation[];
}

interface FetchWeeklyReviewsOptions {
  limit?: number;
}

export async function fetchWeeklyReviews(
  options: FetchWeeklyReviewsOptions = {},
): Promise<WeeklyReviewRun[]> {
  const limit = options.limit ?? 20;
  try {
    const { data } = await runPython<WeeklyReviewRun[]>("scripts.journal_review", {
      args: ["--json", "review", "list", "--limit", String(limit)],
      timeoutMs: 30_000,
    });
    return data;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}
