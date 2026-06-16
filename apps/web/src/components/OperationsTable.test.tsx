import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { OperationsTable } from "./OperationsTable";

const MOCK_REPORT = {
  has_stale: true,
  stale_count: 1,
  fresh_count: 1,
  total_count: 2,
  stale_types: ["alerts"],
  records: [
    { data_type: "provider_health", status: "fresh", last_refreshed_at: new Date().toISOString(), age_seconds: 100, threshold_seconds: 3600 },
    { data_type: "alerts", status: "stale", last_refreshed_at: new Date(Date.now() - 7200000).toISOString(), age_seconds: 7200, threshold_seconds: 3600 },
  ],
};

describe("OperationsTable", () => {
  it("should render all operations grouped by category", () => {
    render(<OperationsTable report={MOCK_REPORT} />);
    expect(screen.getByText("Provider Health")).toBeDefined();
    expect(screen.getByText("Alerts")).toBeDefined();
  });

  it("should show Run Now buttons", () => {
    render(<OperationsTable report={MOCK_REPORT} />);
    const buttons = screen.getAllByRole("button", { name: /run/i });
    expect(buttons.length).toBeGreaterThan(0);
  });
});
