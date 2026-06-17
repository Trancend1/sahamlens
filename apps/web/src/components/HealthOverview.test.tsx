import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { HealthOverview } from "./HealthOverview";
import type { HealthReport } from "@/lib/health";

const MOCK_HEALTHY: HealthReport = {
  overall: "healthy",
  summary: "All required services available.",
  checks: {
    python: { status: "ok", label: "Core Engine", detail: "Python 3.12.7" },
    database: { status: "ok", label: "Database", detail: "Connected" },
    runtime: { status: "ok", label: "Runtime", detail: "Schema ready" },
    llm: { status: "ok", label: "LLM Provider", detail: "openrouter / claude" },
  },
  refresh_mode: "manual",
};

const MOCK_DEGRADED: HealthReport = {
  overall: "degraded",
  summary: "Some non-critical services unavailable.",
  checks: {
    python: { status: "ok", label: "Core Engine", detail: "Python 3.12.7" },
    database: { status: "ok", label: "Database", detail: "Connected" },
    runtime: { status: "ok", label: "Runtime", detail: "Schema ready" },
    llm: { status: "degraded", label: "LLM Provider", detail: "Not configured" },
  },
  refresh_mode: "manual",
};

describe("HealthOverview", () => {
  it("should show healthy status", () => {
    render(<HealthOverview report={MOCK_HEALTHY} />);
    expect(screen.getByText("healthy")).toBeDefined();
    expect(screen.getByText("All required services available.")).toBeDefined();
  });

  it("should show degraded status", () => {
    render(<HealthOverview report={MOCK_DEGRADED} />);
    expect(screen.getByText("degraded")).toBeDefined();
  });

  it("should show all system checks", () => {
    render(<HealthOverview report={MOCK_HEALTHY} />);
    expect(screen.getByText("Core Engine")).toBeDefined();
    expect(screen.getByText("Database")).toBeDefined();
    expect(screen.getByText("Runtime")).toBeDefined();
    expect(screen.getByText("LLM Provider")).toBeDefined();
  });
});
