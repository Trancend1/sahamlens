import { describe, expect, it, vi } from "vitest";

vi.mock("./pythonRunner", () => ({
  runPython: vi.fn(),
  toRuntimeFetchError: vi.fn((error: unknown) => error),
}));

const { runPython } = await import("./pythonRunner");
const runMock = vi.mocked(runPython);

describe("fetchRuntimeStatus", () => {
  it("calls runtime status CLI with JSON output", async () => {
    runMock.mockResolvedValueOnce({
      data: {
        ok: true,
        status: "ready",
        db_path: "data/private/sahamlens.duckdb",
        python_executable: "python",
        applied_migrations: ["0001"],
        pending_migrations: [],
        missing_tables: [],
        schema_status: "ready",
        warnings: [],
        errors: [],
        recommended_commands: [],
      },
      rawStdout: "",
      rawStderr: "",
    });

    const { fetchRuntimeStatus } = await import("./runtime");
    const status = await fetchRuntimeStatus();

    expect(status.schema_status).toBe("ready");
    expect(runMock).toHaveBeenCalledWith("scripts.runtime", {
      args: ["status", "--json"],
      timeoutMs: 30_000,
    });
  });
});
