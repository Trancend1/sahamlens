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

describe("alert fetchers", () => {
  it("lists alert rules through the alerts CLI", async () => {
    runMock.mockResolvedValueOnce({
      data: { ok: true, status: "ok", items: [], warnings: [], errors: [], recommended_commands: [] },
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchAlertRules } = await import("./alerts");

    await fetchAlertRules();

    expect(runMock).toHaveBeenCalledWith("scripts.alerts", {
      args: ["--json", "rules", "list"],
      timeoutMs: 30_000,
    });
  });

  it("lists alert events through the alerts CLI", async () => {
    runMock.mockResolvedValueOnce({
      data: { ok: true, status: "ok", items: [], warnings: [], errors: [], recommended_commands: [] },
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchAlertEvents } = await import("./alerts");

    await fetchAlertEvents();

    expect(runMock).toHaveBeenCalledWith("scripts.alerts", {
      args: ["--json", "events", "list"],
      timeoutMs: 30_000,
    });
  });

  it("evaluates alerts through the alerts CLI", async () => {
    runMock.mockResolvedValueOnce({
      data: {
        ok: true,
        status: "evaluated",
        item: { evaluated_count: 0, event_count: 0, evaluations: [], events: [], warnings: [] },
        warnings: [],
        errors: [],
        recommended_commands: [],
      },
      rawStdout: "",
      rawStderr: "",
    });
    const { evaluateAlerts } = await import("./alerts");

    await evaluateAlerts();

    expect(runMock).toHaveBeenCalledWith("scripts.alerts", {
      args: ["--json", "evaluate"],
      timeoutMs: 30_000,
    });
  });

  it("marks false positive with the correct CLI command", async () => {
    runMock.mockResolvedValueOnce({
      data: { ok: true, status: "mark_false_positive", item: null, warnings: [], errors: [], recommended_commands: [] },
      rawStdout: "",
      rawStderr: "",
    });
    const { markAlertEventFalsePositive } = await import("./alerts");

    await markAlertEventFalsePositive("event-1");

    expect(runMock).toHaveBeenCalledWith("scripts.alerts", {
      args: ["--json", "events", "mark-false-positive", "--event-id", "event-1"],
      timeoutMs: 30_000,
    });
  });

  it("fetches Telegram status without exposing secrets", async () => {
    runMock.mockResolvedValueOnce({
      data: {
        ok: true,
        status: "configured",
        item: {
          enabled: true,
          status: "configured",
          configured: true,
          bot_token_configured: true,
          chat_id_configured: true,
          message: "Telegram delivery is configured.",
        },
        warnings: [],
        errors: [],
        recommended_commands: [],
      },
      rawStdout: "",
      rawStderr: "",
    });
    const { fetchTelegramStatus } = await import("./alerts");

    const status = await fetchTelegramStatus();

    expect(status.enabled).toBe(true);
    expect(JSON.stringify(status)).not.toContain("secret-token");
    expect(runMock).toHaveBeenCalledWith("scripts.alerts", {
      args: ["--json", "telegram", "status"],
      timeoutMs: 30_000,
    });
  });

  it("sends alert event to Telegram through explicit CLI command", async () => {
    runMock.mockResolvedValueOnce({
      data: { ok: true, status: "sent", item: null, warnings: [], errors: [], recommended_commands: [] },
      rawStdout: "",
      rawStderr: "",
    });
    const { sendAlertEventToTelegram } = await import("./alerts");

    await sendAlertEventToTelegram("event-1");

    expect(runMock).toHaveBeenCalledWith("scripts.alerts", {
      args: ["--json", "telegram", "send", "--event-id", "event-1"],
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
          errors: [{ code: "schema_stale", message: "Local alert schema is not ready." }],
          recommended_commands: ["uv run python -m scripts.migrate"],
        }),
        "",
        3,
      ),
    );
    const { fetchAlertRules } = await import("./alerts");

    await expect(fetchAlertRules()).rejects.toMatchObject({
      info: {
        code: "schema_stale",
        recommended_command: "uv run python -m scripts.migrate",
      },
    });
  });
});
