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

    expect(html).toContain("No strategy rules yet");
    expect(html).toContain("Create your first rule");
  });

  it("renders named rules even when no evaluations exist yet", () => {
    const html = renderToStaticMarkup(
      <StrategyRulesDashboard rules={rules} evaluations={[]} error={null} />,
    );

    expect(html).toContain("Stop loss present");
    expect(html).toContain("No rule evaluations yet");
    expect(html).toContain("Evaluate strategy rules");
    expect(html).not.toContain("Gagal membaca strategy rules.");
  });

  it("renders error state", () => {
    const html = renderToStaticMarkup(
      <StrategyRulesDashboard
        rules={[]}
        evaluations={[]}
        error={{
          code: "missing_table",
          message: "Missing runtime table: strategy_rule_evaluations.",
          details: "Run the latest migration before opening Strategy Rules.",
          recommended_command: "uv run python -m scripts.migrate",
        }}
      />,
    );

    expect(html).toContain("Migration required");
    expect(html).toContain("strategy_rule_evaluations");
    expect(html).toContain("Check runtime status");
    expect(html).not.toContain("Traceback");
    expect(html).not.toContain("no such table");
    expect(html).not.toContain("D:/DevSpace");
  });

  it("treats no violations as a valid evaluation state", () => {
    const passed: StrategyRuleEvaluation[] = [
      { ...evaluations[0]!, evaluation_status: "pass", violations: [] },
    ];
    const html = renderToStaticMarkup(
      <StrategyRulesDashboard rules={rules} evaluations={passed} error={null} />,
    );

    expect(html).toContain("Pass");
    expect(html).toContain("No rule violations found");
    expect(html).not.toContain("Gagal membaca strategy rules.");
  });
});
