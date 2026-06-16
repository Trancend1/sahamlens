import { describe, it, expect } from "vitest";

describe("Config flow", () => {
  it("lib/config accessible via api route", async () => {
    const configRoute = await import("@/app/api/config/route");
    expect(configRoute.GET).toBeDefined();
    expect(configRoute.POST).toBeDefined();
  });
});
