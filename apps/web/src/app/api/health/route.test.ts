import { describe, it, expect, vi, beforeEach } from "vitest";
import { GET } from "./route";

vi.mock("@/lib/pythonRunner", () => ({
  runPython: vi.fn(),
  PythonRunnerError: class extends Error {
    constructor(m: string, public stdout = "", public stderr = "", public exitCode: number | null = null) {
      super(m);
      this.name = "PythonRunnerError";
    }
  },
}));

import { runPython } from "@/lib/pythonRunner";

describe("GET /api/health", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return healthy when all checks pass", async () => {
    vi.mocked(runPython).mockResolvedValueOnce({
      data: {
        ok: true, status: "ready", db_path: "data/private/sahamlens.duckdb",
        python_executable: "python3.12", schema_status: "ready",
        applied_migrations: ["001_init"], pending_migrations: [],
        missing_tables: [], warnings: [], errors: [], recommended_commands: [],
      },
      rawStdout: "", rawStderr: "",
    });
    vi.mocked(runPython).mockResolvedValueOnce({
      data: { ok: true, provider: "openrouter", model: "claude", configured: true },
      rawStdout: "", rawStderr: "",
    });

    const res = await GET();
    const body = await res.json();
    expect(body.overall).toBe("healthy");
    expect(body.checks.runtime.status).toBe("ok");
    expect(body.checks.llm.status).toBe("ok");
  });

  it("should return degraded when LLM is not configured", async () => {
    vi.mocked(runPython).mockResolvedValueOnce({
      data: {
        ok: true, status: "ready", db_path: "data/private/sahamlens.duckdb",
        python_executable: "python3.12", schema_status: "ready",
        applied_migrations: ["001_init"], pending_migrations: [],
        missing_tables: [], warnings: [], errors: [], recommended_commands: [],
      },
      rawStdout: "", rawStderr: "",
    });
    vi.mocked(runPython).mockResolvedValueOnce({
      data: { ok: false, provider: "", model: "", configured: false, error: "Not configured" },
      rawStdout: "", rawStderr: "",
    });

    const res = await GET();
    const body = await res.json();
    expect(body.overall).toBe("degraded");
    expect(body.checks.llm.status).toBe("degraded");
  });

  it("should return unhealthy when runtime fails", async () => {
    vi.mocked(runPython).mockRejectedValue(new Error("Python not found"));

    const res = await GET();
    const body = await res.json();
    expect(body.overall).toBe("unhealthy");
    expect(body.checks.runtime.status).toBe("fail");
  });
});
