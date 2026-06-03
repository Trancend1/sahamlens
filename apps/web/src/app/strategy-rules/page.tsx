import { StrategyRulesDashboard } from "@/components/StrategyRulesDashboard";
import {
  fetchStrategyRuleResults,
  fetchStrategyRules,
  type StrategyRule,
  type StrategyRuleEvaluation,
} from "@/lib/strategyRules";
import { normalizeRuntimeError, type RuntimeErrorInfo } from "@/lib/pythonRunner";

export const dynamic = "force-dynamic";

export default async function StrategyRulesPage() {
  let rules: StrategyRule[] = [];
  let evaluations: StrategyRuleEvaluation[] = [];
  let error: RuntimeErrorInfo | null = null;

  try {
    [rules, evaluations] = await Promise.all([
      fetchStrategyRules(),
      fetchStrategyRuleResults(),
    ]);
  } catch (err) {
    error = normalizeRuntimeError(err);
  }

  return <StrategyRulesDashboard rules={rules} evaluations={evaluations} error={error} />;
}
