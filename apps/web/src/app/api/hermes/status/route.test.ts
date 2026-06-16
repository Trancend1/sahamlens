import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("node:fs", () => {
  const mock = {
    existsSync: vi.fn(),
    readFileSync: vi.fn(),
  };
  return Object.assign(mock, { default: mock });
});

describe("GET /api/hermes/status", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  it("should return disabled config when not enabled", async () => {
    const { GET } = await import("./route");
    const response = await GET();
    const body = await response.json();
    expect(body.config.enabled).toBe(false);
    expect(body.config.telegramConfigured).toBe(false);
  });

  it("should show enabled config", async () => {
    vi.stubEnv("SAHAMLENS_HERMES_ENABLED", "1");
    vi.stubEnv("SAHAMLENS_LLM_PROVIDER", "anthropic");
    vi.stubEnv("ANTHROPIC_API_KEY", "sk-ant-test");

    const { GET } = await import("./route");
    const response = await GET();
    const body = await response.json();
    expect(body.config.enabled).toBe(true);
    expect(body.config.providerName).toBe("anthropic");
    expect(body.config.providerConfigured).toBe(true);
  });

  it("should detect running process from pid file", async () => {
    const fs = await import("node:fs");
    vi.mocked(fs.existsSync).mockReturnValue(true);
    vi.mocked(fs.readFileSync).mockReturnValue("99999");

    vi.stubEnv("SAHAMLENS_HERMES_ENABLED", "1");

    const { GET } = await import("./route");
    const response = await GET();
    const body = await response.json();
    expect(body.process.running).toBe(false);
    expect(body.process.pid).toBeNull();
  });
});
