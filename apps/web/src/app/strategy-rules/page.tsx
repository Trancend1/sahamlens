import { StrategyRulesDashboard } from "@/components/StrategyRulesDashboard";
import {
  fetchStrategyRuleResults,
  fetchStrategyRules,
  type StrategyRule,
  type StrategyRuleEvaluation,
} from "@/lib/strategyRules";

export const dynamic = "force-dynamic";

export default async function StrategyRulesPage() {
  let rules: StrategyRule[] = [];
  let evaluations: StrategyRuleEvaluation[] = [];
  let error: string | null = null;

  try {
    [rules, evaluations] = await Promise.all([
      fetchStrategyRules(),
      fetchStrategyRuleResults(),
    ]);
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  return <StrategyRulesDashboard rules={rules} evaluations={evaluations} error={error} />;
}
