import { describe, expect, it, vi } from "vitest";
import EarningsPage from "./page";

vi.mock("@/components/EarningsDashboard", () => ({
  EarningsDashboard: () => <div>Earnings dashboard</div>,
}));

vi.mock("@/lib/earnings", () => ({
  fetchEarningsEvents: vi.fn(),
  fetchEarningsSummaries: vi.fn(),
}));

vi.mock("./actions", () => ({
  archiveEarningsEventAction: vi.fn(),
  createEarningsEventAction: vi.fn(),
  generateEarningsSummaryAction: vi.fn(),
  updateEarningsNotesAction: vi.fn(),
}));

const { fetchEarningsEvents, fetchEarningsSummaries } = await import("@/lib/earnings");
const fetchEarningsEventsMock = vi.mocked(fetchEarningsEvents);
const fetchEarningsSummariesMock = vi.mocked(fetchEarningsSummaries);

describe("EarningsPage", () => {
  it("loads DB-backed earnings fetches sequentially during render", async () => {
    const calls: string[] = [];
    const eventsGate = deferred<Awaited<ReturnType<typeof fetchEarningsEvents>>>();
    fetchEarningsEventsMock.mockImplementation(() => {
      calls.push("events");
      return eventsGate.promise;
    });
    fetchEarningsSummariesMock.mockImplementation(async () => {
      calls.push("summaries");
      return [];
    });

    const page = EarningsPage();
    await Promise.resolve();

    expect(calls).toEqual(["events"]);

    eventsGate.resolve([]);
    await page;

    expect(calls).toEqual(["events", "summaries"]);
  });
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}
