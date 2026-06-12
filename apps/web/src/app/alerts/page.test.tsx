import { describe, expect, it, vi } from "vitest";
import AlertsPage from "./page";

vi.mock("@/components/AlertsDashboard", () => ({
  AlertsDashboard: () => <div>Alerts dashboard</div>,
}));

vi.mock("@/lib/alerts", () => ({
  fetchAlertRules: vi.fn(),
  fetchAlertEvents: vi.fn(),
  fetchTelegramStatus: vi.fn(),
}));

vi.mock("./actions", () => ({
  acknowledgeAlertEventAction: vi.fn(),
  archiveAlertRuleAction: vi.fn(),
  createAlertRuleAction: vi.fn(),
  dismissAlertEventAction: vi.fn(),
  evaluateAlertsAction: vi.fn(),
  markFalsePositiveAction: vi.fn(),
  pauseAlertRuleAction: vi.fn(),
  sendTelegramAction: vi.fn(),
}));

const { fetchAlertRules, fetchAlertEvents, fetchTelegramStatus } = await import("@/lib/alerts");
const fetchAlertRulesMock = vi.mocked(fetchAlertRules);
const fetchAlertEventsMock = vi.mocked(fetchAlertEvents);
const fetchTelegramStatusMock = vi.mocked(fetchTelegramStatus);

describe("AlertsPage", () => {
  it("loads DB-backed alert fetches sequentially during render", async () => {
    const calls: string[] = [];
    const rulesGate = deferred<Awaited<ReturnType<typeof fetchAlertRules>>>();
    fetchAlertRulesMock.mockImplementation(() => {
      calls.push("rules");
      return rulesGate.promise;
    });
    fetchAlertEventsMock.mockImplementation(async () => {
      calls.push("events");
      return [];
    });
    fetchTelegramStatusMock.mockImplementation(async () => {
      calls.push("telegram");
      return {
        enabled: false,
        configured: false,
        status: "not_configured",
        bot_token_configured: false,
        chat_id_configured: false,
        message: "Telegram delivery is optional and not configured.",
      };
    });

    const page = AlertsPage();
    await Promise.resolve();

    expect(calls).toEqual(["rules"]);

    rulesGate.resolve([]);
    await page;

    expect(calls).toEqual(["rules", "events", "telegram"]);
  });
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}
