import { describe, it, expect } from "vitest";
import { OPERATIONS, getOperation, getOperationsByCategory } from "./operations";

describe("operations registry", () => {
  it("should have all expected operations", () => {
    expect(OPERATIONS).toHaveLength(8);
    const ids = OPERATIONS.map((o) => o.id);
    expect(ids).toContain("provider_health");
    expect(ids).toContain("prices");
    expect(ids).toContain("fundamentals");
    expect(ids).toContain("news");
    expect(ids).toContain("alerts");
    expect(ids).toContain("screener");
    expect(ids).toContain("strategy_rules");
    expect(ids).toContain("weekly_review");
  });

  it("each operation should have required fields", () => {
    for (const op of OPERATIONS) {
      expect(op.id).toBeTruthy();
      expect(op.name).toBeTruthy();
      expect(op.description).toBeTruthy();
      expect(op.category).toBeTruthy();
      expect(op.route).toMatch(/^\/api\//);
      expect(op.freshnessKey).toBeTruthy();
      expect(op.timeoutMs).toBeGreaterThan(0);
    }
  });

  it("should retrieve operation by id", () => {
    const op = getOperation("prices");
    expect(op?.id).toBe("prices");
    expect(op?.name).toBe("Refresh Prices");
  });

  it("should return undefined for unknown id", () => {
    expect(getOperation("nonexistent")).toBeUndefined();
  });

  it("should group operations by category", () => {
    const byCat = getOperationsByCategory();
    expect(byCat.provider).toHaveLength(4);
    expect(byCat.analysis).toHaveLength(2);
    expect(byCat.review).toHaveLength(2);
  });
});
