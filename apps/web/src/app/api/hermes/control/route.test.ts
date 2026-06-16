import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest } from "next/server";

vi.mock("node:fs", () => {
  const mock = {
    existsSync: vi.fn(),
    readFileSync: vi.fn(),
    writeFileSync: vi.fn(),
    unlinkSync: vi.fn(),
    openSync: vi.fn(() => 3),
  };
  return Object.assign(mock, { default: mock });
});

vi.mock("node:child_process", () => {
  const mock = {
    spawn: vi.fn(),
    execSync: vi.fn(),
  };
  return Object.assign(mock, { default: mock });
});

function mockJsonBody(action: string): NextRequest {
  return { json: () => Promise.resolve({ action }) } as unknown as NextRequest;
}

describe("POST /api/hermes/control", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should reject invalid action", async () => {
    const { POST } = await import("./route");
    const req = mockJsonBody("restart");
    const response = await POST(req);
    expect(response.status).toBe(400);
    const body = await response.json();
    expect(body.ok).toBe(false);
  });

  it("should start hermes when not running", async () => {
    const fs = await import("node:fs");
    vi.mocked(fs.existsSync).mockReturnValue(false);

    const mockChild = { pid: 12345, unref: vi.fn() };
    const cp = await import("node:child_process");
    vi.mocked(cp.spawn).mockReturnValue(mockChild as unknown as ReturnType<typeof import("node:child_process")["spawn"]>);

    const { POST } = await import("./route");
    const req = mockJsonBody("start");
    const response = await POST(req);
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.ok).toBe(true);
    expect(body.message).toContain("12345");
  });

  it("should stop hermes when running", async () => {
    const fs = await import("node:fs");
    vi.mocked(fs.existsSync).mockReturnValue(true);
    vi.mocked(fs.readFileSync).mockReturnValue("12345");

    const { POST } = await import("./route");
    const req = mockJsonBody("stop");
    const response = await POST(req);
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.ok).toBe(true);
  });

  it("should reject stop when not running", async () => {
    const fs = await import("node:fs");
    vi.mocked(fs.existsSync).mockReturnValue(false);

    const { POST } = await import("./route");
    const req = mockJsonBody("stop");
    const response = await POST(req);
    expect(response.status).toBe(409);
    const body = await response.json();
    expect(body.ok).toBe(false);
  });
});
