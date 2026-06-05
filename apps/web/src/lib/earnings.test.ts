import { describe, expect, it, vi } from "vitest";
import { PythonRunnerError } from "./pythonRunner";

vi.mock("./pythonRunner", async () => {
  const actual = await vi.importActual<typeof import("./pythonRunner")>("./pythonRunner");
  return {
    ...actual,
    runPython: vi.fn(),
  };
});

const { runPython } = await import("./pythonRunner");
const runMock = vi.mocked(runPython);

describe("earnings fetchers", () => {
  it("lists earnings events through the earnings CLI", async () => {
    runMock.mockResolvedValueOnce({
      data: { ok: true, status: "ok", items: [], warnings: [], errors: [], recommended_commands: [] },
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchEarningsEvents } = await import("./earnings");

    await fetchEarningsEvents();

    expect(runMock).toHaveBeenCalledWith("scripts.earnings", {
      args: ["--json", "events", "list"],
      timeoutMs: 30_000,
    });
  });

  it("creates earnings event through the earnings CLI", async () => {
    runMock.mockResolvedValueOnce({
      data: { ok: true, status: "created", item: null, warnings: [], errors: [], recommended_commands: [] },
      rawStdout: "",
      rawStderr: "",
    });
    const { createEarningsEvent } = await import("./earnings");

    await createEarningsEvent({
      ticker: "BBCA",
      period: "2026-Q2",
      eventDate: "2026-07-31",
      sourceType: "manual",
      notes: "Manual notes.",
    });

    expect(runMock).toHaveBeenCalledWith("scripts.earnings", {
      args: [
        "--json",
        "events",
        "create",
        "--ticker",
        "BBCA",
        "--period",
        "2026-Q2",
        "--event-date",
        "2026-07-31",
        "--source-type",
        "manual",
        "--notes",
        "Manual notes.",
      ],
      timeoutMs: 30_000,
    });
  });

  it("generates earnings summary through the earnings CLI", async () => {
    runMock.mockResolvedValueOnce({
      data: { ok: true, status: "generated", item: null, warnings: [], errors: [], recommended_commands: [] },
      rawStdout: "",
      rawStderr: "",
    });
    const { generateEarningsSummary } = await import("./earnings");

    await generateEarningsSummary("event-1");

    expect(runMock).toHaveBeenCalledWith("scripts.earnings", {
      args: ["--json", "summary", "generate", "--event-id", "event-1"],
      timeoutMs: 30_000,
    });
  });

  it("maps missing schema to migration required", async () => {
    runMock.mockRejectedValueOnce(
      new PythonRunnerError(
        "Command failed",
        JSON.stringify({
          ok: false,
          status: "schema_stale",
          errors: [{ code: "schema_stale", message: "Local earnings schema is not ready." }],
          recommended_commands: ["uv run python -m scripts.migrate"],
        }),
        "",
        3,
      ),
    );
    const { fetchEarningsEvents } = await import("./earnings");

    await expect(fetchEarningsEvents()).rejects.toMatchObject({
      info: {
        code: "schema_stale",
        recommended_command: "uv run python -m scripts.migrate",
      },
    });
  });
});
