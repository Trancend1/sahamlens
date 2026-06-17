import { describe, it, expect, vi, beforeEach } from "vitest";
import type { NextRequest } from "next/server";
import { POST } from "./route";

vi.mock("@/lib/cliCommands", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/cliCommands")>();
  return { ...actual, runCli: vi.fn() };
});

import { runCli } from "@/lib/cliCommands";

function makeReq(type: string): NextRequest {
  return new Request(`http://localhost/api/operations/${type}/run`, {
    method: "POST",
  }) as unknown as NextRequest;
}

describe("POST /api/operations/[type]/run", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("runs provider_health via the correct CLI command key", async () => {
    vi.mocked(runCli).mockResolvedValue({ ok: true, data: { ok: true }, stdout: "", stderr: "" });

    const res = await POST(makeReq("provider_health"), {
      params: Promise.resolve({ type: "provider_health" }),
    });
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(runCli).toHaveBeenCalledWith("provider_health.refresh", expect.any(Object));
  });

  it("runs prices via the correct CLI command key", async () => {
    vi.mocked(runCli).mockResolvedValue({ ok: true, data: { ok: true }, stdout: "", stderr: "" });

    const res = await POST(makeReq("prices"), { params: Promise.resolve({ type: "prices" }) });
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(runCli).toHaveBeenCalledWith("prices.refresh", expect.objectContaining({ fromWatchlist: true }));
  });

  it("returns 400 for unknown operation type", async () => {
    const res = await POST(makeReq("unknown"), { params: Promise.resolve({ type: "unknown" }) });
    expect(res.status).toBe(400);
  });

  it("returns 500 when the CLI fails", async () => {
    vi.mocked(runCli).mockRejectedValue(new Error("yfinance timeout"));

    const res = await POST(makeReq("provider_health"), {
      params: Promise.resolve({ type: "provider_health" }),
    });
    expect(res.status).toBe(500);
    const body = await res.json();
    expect(body.ok).toBe(false);
  });
});
