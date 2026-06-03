import { describe, expect, it, vi } from "vitest";

vi.mock("./pythonRunner", () => ({
  runPython: vi.fn(),
}));

const { runPython } = await import("./pythonRunner");
const runMock = vi.mocked(runPython);

describe("strategy rule fetchers", () => {
  it("fetches active simple rules from the journal review CLI", async () => {
    runMock.mockResolvedValueOnce({
      data: [],
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchStrategyRules } = await import("./strategyRules");

    await fetchStrategyRules();

    expect(runMock).toHaveBeenCalledWith("scripts.journal_review", {
      args: ["--json", "rules", "list", "--active-only"],
      timeoutMs: 30_000,
    });
  });

  it("fetches persisted strategy rule evaluation results", async () => {
    runMock.mockResolvedValueOnce({
      data: [],
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchStrategyRuleResults } = await import("./strategyRules");

    await fetchStrategyRuleResults({ reviewId: "review-1" });

    expect(runMock).toHaveBeenCalledWith("scripts.journal_review", {
      args: ["--json", "rules", "results", "--review-id", "review-1"],
      timeoutMs: 30_000,
    });
  });
});
