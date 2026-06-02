import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { StrategyRule, StrategyRuleEvaluation } from "@/lib/strategyRules";
import { StrategyRulesDashboard } from "./StrategyRulesDashboard";

const rules: StrategyRule[] = [
  {
    rule_id: "stop_loss_present",
    name: "Stop loss present",
    description: "Checks that each journal plan records a stop level.",
    rule_category: "risk_discipline",
    required_fields: ["stop_level"],
    violation_code: "missing_stop_loss",
    needs_data_behavior: "needs_data",
    is_active: true,
    created_at: "2026-06-02T10:00:00Z",
    updated_at: "2026-06-02T10:00:00Z",
  },
];

const evaluations: StrategyRuleEvaluation[] = [
  {
    evaluation_id: "evaluation-1",
    review_id: "review-1",
    rule_id: "stop_loss_present",
    journal_id: 1,
    symbol: "BBCA.JK",
    evaluation_status: "fail",
    evaluated_at: "2026-06-02T10:00:00Z",
    evidence: ["BBCA.JK journal 1 is missing stop_level."],
    caveats: ["Rule failed because required journal fields were missing or empty."],
    reason: "Stop loss present failed for BBCA.JK: missing stop_level.",
    violations: [
      {
        violation_id: "violation-1",
        evaluation_id: "evaluation-1",
        review_id: "review-1",
        rule_id: "stop_loss_present",
        journal_id: 1,
        symbol: "BBCA.JK",
        violation_code: "missing_stop_loss",
        violation_detail: "BBCA.JK journal 1 is missing stop_level.",
        evidence: ["BBCA.JK journal 1 is missing stop_level."],
        caveats: ["Rule violations are journal hygiene checks, not trade signals."],
        created_at: "2026-06-02T10:00:00Z",
      },
    ],
  },
];

describe("StrategyRulesDashboard", () => {
  it("renders named rules, evaluation status, violation reasons, and no-DSL copy", () => {
    const html = renderToStaticMarkup(
      <StrategyRulesDashboard rules={rules} evaluations={evaluations} error={null} />,
    );

    expect(html).toContain("Strategy Rules");
    expect(html).toContain("Stop loss present");
    expect(html).toContain("Fail");
    expect(html).toContain("missing_stop_loss");
    expect(html).toContain("No custom DSL");
    expect(html).toContain("not trade signals");
  });

  it("renders empty state", () => {
    const html = renderToStaticMarkup(
      <StrategyRulesDashboard rules={[]} evaluations={[]} error={null} />,
    );

    expect(html).toContain("Belum ada strategy-rule data.");
    expect(html).toContain("scripts.journal_review");
  });

  it("renders error state", () => {
    const html = renderToStaticMarkup(
      <StrategyRulesDashboard rules={[]} evaluations={[]} error="missing strategy_rules" />,
    );

    expect(html).toContain("Gagal membaca strategy rules.");
    expect(html).toContain("missing strategy_rules");
  });
});
