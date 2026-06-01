import { describe, expect, it, vi } from "vitest";

vi.mock("./pythonRunner", () => ({
  runPython: vi.fn(),
}));

const { runPython } = await import("./pythonRunner");
const runMock = vi.mocked(runPython);

describe("fetchFundamentalSnapshot", () => {
  it("calls fundamentals snapshot CLI and returns parsed overview", async () => {
    runMock.mockResolvedValueOnce({
      data: {
        symbol: "BBCA.JK",
        coverage: null,
        fundamental: null,
        source_coverage: [],
      },
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchFundamentalSnapshot } = await import("./fundamentals");

    const overview = await fetchFundamentalSnapshot("BBCA");

    expect(overview.symbol).toBe("BBCA.JK");
    expect(runMock).toHaveBeenCalledWith("scripts.fundamentals", {
      args: ["--json", "snapshot", "--symbol", "BBCA"],
      timeoutMs: 30_000,
    });
  });
});
