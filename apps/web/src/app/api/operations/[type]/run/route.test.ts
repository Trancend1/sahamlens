import { describe, it, expect, vi, beforeEach } from "vitest";
import { POST } from "./route";

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

describe("POST /api/operations/[type]/run", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should run provider_health operation", async () => {
    vi.mocked(runPython).mockResolvedValue({
      data: { ok: true },
      rawStdout: "",
      rawStderr: "",
    });

    const req = new Request("http://localhost/api/operations/provider_health/run", { method: "POST" });
    const res = await POST(req, { params: Promise.resolve({ type: "provider_health" }) });
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(runPython).toHaveBeenCalledWith("scripts.provider_health", expect.any(Object));
  });

  it("should run prices operation with correct module", async () => {
    vi.mocked(runPython).mockResolvedValue({
      data: { ok: true },
      rawStdout: "",
      rawStderr: "",
    });

    const req = new Request("http://localhost/api/operations/prices/run", { method: "POST" });
    const res = await POST(req, { params: Promise.resolve({ type: "prices" }) });
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(runPython).toHaveBeenCalledWith("scripts.ingest_prices", expect.any(Object));
  });

  it("should return 400 for unknown operation type", async () => {
    const req = new Request("http://localhost/api/operations/unknown/run", { method: "POST" });
    const res = await POST(req, { params: Promise.resolve({ type: "unknown" }) });
    expect(res.status).toBe(400);
  });

  it("should return 500 on Python error", async () => {
    vi.mocked(runPython).mockRejectedValue(new Error("yfinance timeout"));

    const req = new Request("http://localhost/api/operations/provider_health/run", { method: "POST" });
    const res = await POST(req, { params: Promise.resolve({ type: "provider_health" }) });
    expect(res.status).toBe(500);
    const body = await res.json();
    expect(body.ok).toBe(false);
  });
});
