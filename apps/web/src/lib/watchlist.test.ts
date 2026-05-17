import { describe, expect, it, vi } from "vitest";

vi.mock("./pythonRunner", () => ({
  runPython: vi.fn(),
}));

const { runPython } = await import("./pythonRunner");
const runMock = vi.mocked(runPython);

describe("fetchWatchlist", () => {
  it("calls scripts.watchlist with --json list and returns parsed entries", async () => {
    runMock.mockResolvedValueOnce({
      data: [
        { symbol: "BBCA.JK", tag: "bank-core", note: null, added_at: "2026-05-01T08:00:00+07:00" },
      ],
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchWatchlist } = await import("./watchlist");

    const entries = await fetchWatchlist();

    expect(entries).toHaveLength(1);
    expect(entries[0]?.symbol).toBe("BBCA.JK");
    expect(runMock).toHaveBeenCalledWith("scripts.watchlist", { args: ["--json", "list"] });
  });
});
