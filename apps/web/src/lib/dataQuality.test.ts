import { describe, expect, it, vi } from "vitest";

vi.mock("./pythonRunner", () => ({
  runPython: vi.fn(),
}));

const { runPython } = await import("./pythonRunner");
const runMock = vi.mocked(runPython);

describe("fetchDataQualityOverview", () => {
  it("calls provider health list CLI and returns parsed overview", async () => {
    runMock.mockResolvedValueOnce({
      data: {
        providers: [],
        provider_count: 0,
        failed_provider_count: 0,
        stale_provider_count: 0,
        restricted_provider_count: 0,
        total_coverage_count: 0,
      },
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchDataQualityOverview } = await import("./dataQuality");

    const overview = await fetchDataQualityOverview();

    expect(overview.provider_count).toBe(0);
    expect(runMock).toHaveBeenCalledWith("scripts.provider_health", {
      args: ["--json", "list"],
    });
  });
});
