import { describe, expect, it, vi } from "vitest";

vi.mock("./pythonRunner", () => ({
  runPython: vi.fn(),
}));

const { runPython } = await import("./pythonRunner");
const runMock = vi.mocked(runPython);

describe("fetchWeeklyReviews", () => {
  it("calls the journal review CLI with JSON list output", async () => {
    runMock.mockResolvedValueOnce({
      data: [],
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchWeeklyReviews } = await import("./journalReview");

    const reviews = await fetchWeeklyReviews({ limit: 5 });

    expect(reviews).toEqual([]);
    expect(runMock).toHaveBeenCalledWith("scripts.journal_review", {
      args: ["--json", "review", "list", "--limit", "5"],
      timeoutMs: 30_000,
    });
  });
});
