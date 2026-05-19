import { describe, expect, it } from "vitest";
import { formatRelativeTime, freshnessTier } from "./dateTime";

const FIXED_NOW = new Date("2026-05-18T12:00:00Z");

describe("formatRelativeTime", () => {
  it("formats minutes ago", () => {
    const out = formatRelativeTime("2026-05-18T11:30:00Z", FIXED_NOW);
    expect(out.toLowerCase()).toContain("menit");
  });

  it("formats hours ago", () => {
    const out = formatRelativeTime("2026-05-18T09:00:00Z", FIXED_NOW);
    expect(out.toLowerCase()).toContain("jam");
  });

  it("formats days ago", () => {
    const out = formatRelativeTime("2026-05-13T12:00:00Z", FIXED_NOW);
    expect(out.toLowerCase()).toContain("hari");
  });

  it("returns original string when input invalid", () => {
    expect(formatRelativeTime("not-a-date", FIXED_NOW)).toBe("not-a-date");
  });
});

describe("freshnessTier", () => {
  it("fresh under 24h", () => {
    expect(freshnessTier("2026-05-18T11:00:00Z", FIXED_NOW)).toBe("fresh");
  });

  it("stale 24-72h", () => {
    expect(freshnessTier("2026-05-16T12:00:00Z", FIXED_NOW)).toBe("stale");
  });

  it("old beyond 72h", () => {
    expect(freshnessTier("2026-05-10T12:00:00Z", FIXED_NOW)).toBe("old");
  });

  it("old on invalid input", () => {
    expect(freshnessTier("garbage", FIXED_NOW)).toBe("old");
  });
});
