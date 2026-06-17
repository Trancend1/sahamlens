import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest } from "next/server";
import { GET, POST } from "./route";

vi.mock("node:fs", () => {
  const mockFs = {
    existsSync: vi.fn(),
    readFileSync: vi.fn(),
    writeFileSync: vi.fn(),
  };
  return { ...mockFs, default: mockFs };
});

import fs from "node:fs";

const mockEnv = `SAHAMLENS_LLM_PROVIDER=openrouter
SAHAMLENS_LLM_BASE_URL=https://openrouter.ai/api/v1
SAHAMLENS_LLM_MODEL=anthropic/claude-sonnet-4-6
DUCKDB_PATH=./data/private/sahamlens.duckdb
`;

describe("GET /api/config", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fs.existsSync).mockReturnValue(true);
    vi.mocked(fs.readFileSync).mockReturnValue(mockEnv);
  });

  it("should return LLM config section", async () => {
    const req = new NextRequest("http://localhost/api/config?section=llm");
    const res = await GET(req);
    const body = await res.json();
    expect(body.section).toBe("llm");
    expect(body.config.provider).toBe("openrouter");
    expect(body.config.baseUrl).toBe("https://openrouter.ai/api/v1");
    expect(body.config.model).toBe("anthropic/claude-sonnet-4-6");
  });

  it("should return app config section", async () => {
    const req = new NextRequest("http://localhost/api/config?section=app");
    const res = await GET(req);
    const body = await res.json();
    expect(body.section).toBe("app");
    expect(body.config.dataDir).toBe("./data/private/sahamlens.duckdb");
  });

  it("should return 400 for unknown section", async () => {
    const req = new NextRequest("http://localhost/api/config?section=unknown");
    const res = await GET(req);
    expect(res.status).toBe(400);
  });
});

describe("POST /api/config", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fs.existsSync).mockReturnValue(true);
    vi.mocked(fs.readFileSync).mockReturnValue(mockEnv);
  });

  it("should update LLM config", async () => {
    const req = new NextRequest("http://localhost/api/config?section=llm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: "anthropic",
        model: "claude-sonnet-4-20250514",
        baseUrl: "",
        apiKey: "sk-ant-new-key", // pragma: allowlist secret
      }),
    });
    const res = await POST(req);
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(fs.writeFileSync).toHaveBeenCalled();
  });

  it("should return 400 for missing section", async () => {
    const req = new NextRequest("http://localhost/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
  });

  it("should return 400 for app section (read-only)", async () => {
    const req = new NextRequest("http://localhost/api/config?section=app", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataDir: "/new/path" }),
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body.error).toContain("read-only");
  });
});
