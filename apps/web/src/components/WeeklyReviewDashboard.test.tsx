import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { WeeklyReviewRun } from "@/lib/journalReview";
import { WeeklyReviewDashboard } from "./WeeklyReviewDashboard";

const review: WeeklyReviewRun = {
  review_id: "review-1",
  period_start: "2026-05-25T00:00:00Z",
  period_end: "2026-06-01T23:59:59Z",
  generated_at: "2026-06-02T10:00:00Z",
  status: "completed",
  journal_entry_count: 2,
  reviewed_plan_count: 2,
  rule_evaluation_count: 12,
  violation_count: 3,
  needs_data_count: 0,
  summary: "Weekly review: 2 journal plan(s), 12 rule evaluation(s), 3 violation(s).",
  evidence: ["BBCA.JK journal 1 status planned"],
  caveats: ["Weekly review is behavior reflection only and is not financial advice."],
  findings: [
    {
      finding_id: "finding-1",
      review_id: "review-1",
      finding_type: "rule_violation",
      title: "missing_stop_loss repeated 1 time(s)",
      detail: "missing_stop_loss: BBCA.JK journal 2 is missing stop_level.",
      severity: "warning",
      evidence: ["BBCA.JK journal 2 is missing stop_level."],
      caveats: ["Rule violations are journal hygiene checks, not trade signals."],
      created_at: "2026-06-02T10:00:00Z",
    },
  ],
  rule_evaluations: [],
};

describe("WeeklyReviewDashboard", () => {
  it("renders summary cards, findings, evidence, and caveats", () => {
    const html = renderToStaticMarkup(<WeeklyReviewDashboard reviews={[review]} error={null} />);

    expect(html).toContain("Weekly Journal Review");
    expect(html).toContain("2");
    expect(html).toContain("missing_stop_loss repeated");
    expect(html).toContain("Evidence");
    expect(html).toContain("Caveats");
    expect(html).toContain("behavior reflection only");
  });

  it("renders empty state with local CLI path", () => {
    const html = renderToStaticMarkup(<WeeklyReviewDashboard reviews={[]} error={null} />);

    expect(html).toContain("Belum ada weekly review.");
    expect(html).toContain("scripts.journal_review");
  });

  it("renders error state", () => {
    const html = renderToStaticMarkup(
      <WeeklyReviewDashboard reviews={[]} error="missing weekly_review_runs" />,
    );

    expect(html).toContain("Gagal membaca weekly review.");
    expect(html).toContain("missing weekly_review_runs");
  });
});
