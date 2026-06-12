import { describe, expect, it, vi } from "vitest";
import StrategyRulesPage from "./page";

vi.mock("@/components/StrategyRulesDashboard", () => ({
  StrategyRulesDashboard: () => <div>Strategy rules dashboard</div>,
}));

vi.mock("@/lib/strategyRules", () => ({
  fetchStrategyRuleResults: vi.fn(),
  fetchStrategyRules: vi.fn(),
}));

const { fetchStrategyRuleResults, fetchStrategyRules } = await import("@/lib/strategyRules");
const fetchStrategyRuleResultsMock = vi.mocked(fetchStrategyRuleResults);
const fetchStrategyRulesMock = vi.mocked(fetchStrategyRules);

describe("StrategyRulesPage", () => {
  it("loads DB-backed strategy rule fetches sequentially during render", async () => {
    const calls: string[] = [];
    const rulesGate = deferred<Awaited<ReturnType<typeof fetchStrategyRules>>>();
    fetchStrategyRulesMock.mockImplementation(() => {
      calls.push("rules");
      return rulesGate.promise;
    });
    fetchStrategyRuleResultsMock.mockImplementation(async () => {
      calls.push("results");
      return [];
    });

    const page = StrategyRulesPage();
    await Promise.resolve();

    expect(calls).toEqual(["rules"]);

    rulesGate.resolve([]);
    await page;

    expect(calls).toEqual(["rules", "results"]);
  });
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}
