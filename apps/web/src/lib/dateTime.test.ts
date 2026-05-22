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

  // IDX weekend gap: Friday close → Monday morning is ~65h → stale (not old)
  // IDX closes Friday 4pm WIB (UTC+7) = 9am UTC. Monday 9am WIB = 2am UTC.
  // Diff ≈ 65h → stale. This is expected and acceptable.
  it("IDX Friday close data is stale (not old) on Monday morning", () => {
    const fridayClose = new Date("2026-05-15T09:00:00Z"); // Friday 4pm WIB
    const mondayMorning = new Date("2026-05-18T02:00:00Z"); // Monday 9am WIB
    expect(freshnessTier(fridayClose.toISOString(), mondayMorning)).toBe("stale");
  });

  it("date-only string (YYYY-MM-DD) is treated as midnight UTC", () => {
    // 2026-05-18 midnight UTC is 12h before FIXED_NOW (2026-05-18T12:00:00Z) → fresh
    expect(freshnessTier("2026-05-18", FIXED_NOW)).toBe("fresh");
  });

  it("timestamp with UTC+7 offset parses correctly", () => {
    // 2026-05-18T18:00:00+07:00 = 11:00:00Z, which is 1h before FIXED_NOW → fresh
    expect(freshnessTier("2026-05-18T18:00:00+07:00", FIXED_NOW)).toBe("fresh");
  });
});
