import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { EarningsEvent, EarningsSummary } from "@/lib/earnings";
import type { RuntimeErrorInfo } from "@/lib/pythonRunner";
import { EarningsDashboard } from "./EarningsDashboard";

const event: EarningsEvent = {
  id: "event-1",
  ticker: "BBCA.JK",
  period: "2026-Q2",
  event_date: "2026-07-31",
  source_type: "manual",
  source_ref: "owner note",
  status: "summarized",
  created_at: "2026-06-05T10:00:00Z",
  updated_at: "2026-06-05T10:10:00Z",
  notes: "Revenue grew compared with prior quarter. Margin pressure remains a caveat.",
};

const summary: EarningsSummary = {
  id: "summary-1",
  earnings_event_id: "event-1",
  generated_at: "2026-06-05T10:15:00Z",
  summary_text: "Post-event review for BBCA.JK 2026-Q2 based on manual notes.",
  caveats: ["Based on manual notes and available local data; not an instruction."],
  input_snapshot: { ticker: "BBCA.JK", period: "2026-Q2" },
  confidence_status: "manual_only",
};

describe("EarningsDashboard", () => {
  it("renders page header and safe copy", () => {
    const html = renderToStaticMarkup(
      <EarningsDashboard events={[event]} summaries={[summary]} error={null} />,
    );

    expect(html).toContain("Earnings");
    expect(html).toContain("Track earnings events manually");
    expect(html).toContain("not predictions or instructions");
    expect(html).not.toContain("buy");
    expect(html).not.toContain("sell");
    expect(html).not.toContain("profit opportunity");
  });

  it("renders no events empty state and create form", () => {
    const html = renderToStaticMarkup(
      <EarningsDashboard events={[]} summaries={[]} error={null} />,
    );

    expect(html).toContain("No earnings events yet");
    expect(html).toContain("Add earnings event");
    expect(html).toContain("Create Earnings Event");
  });

  it("renders event list and no summary state", () => {
    const html = renderToStaticMarkup(
      <EarningsDashboard events={[{ ...event, status: "planned" }]} summaries={[]} error={null} />,
    );

    expect(html).toContain("BBCA.JK");
    expect(html).toContain("2026-Q2");
    expect(html).toContain("No summary generated yet");
    expect(html).toContain("Generate summary");
  });

  it("renders summary detail with caveats and input snapshot", () => {
    const html = renderToStaticMarkup(
      <EarningsDashboard events={[event]} summaries={[summary]} error={null} />,
    );

    expect(html).toContain("Post-event review for BBCA.JK");
    expect(html).toContain("Caveats");
    expect(html).toContain("manual_only");
    expect(html).toContain("Input snapshot");
  });

  it("renders migration required state without raw traceback", () => {
    const error: RuntimeErrorInfo = {
      code: "schema_stale",
      message: "Local earnings schema is not ready.",
      details: "Run migration before using earnings.",
      recommended_command: "uv run python -m scripts.migrate",
    };
    const html = renderToStaticMarkup(
      <EarningsDashboard events={[]} summaries={[]} error={error} />,
    );

    expect(html).toContain("Migration required");
    expect(html).toContain("scripts.migrate");
    expect(html).not.toContain("Traceback");
    expect(html).not.toContain("no such table");
    expect(html).not.toContain("D:/DevSpace");
  });
});
