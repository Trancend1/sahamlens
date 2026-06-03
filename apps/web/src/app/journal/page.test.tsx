import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fetchPlans } from "@/lib/journal";
import JournalPage from "./page";

vi.mock("@/lib/journal", () => ({
  fetchPlans: vi.fn(),
}));

const mockedFetchPlans = vi.mocked(fetchPlans);

describe("JournalPage", () => {
  beforeEach(() => {
    mockedFetchPlans.mockReset();
  });

  it("renders actionable empty state for an empty journal", async () => {
    mockedFetchPlans.mockResolvedValue([]);

    const html = renderToStaticMarkup(await JournalPage());

    expect(html).toContain("No journal entries yet");
    expect(html).toContain("Add journal entry");
    expect(html).not.toContain("Traceback");
  });

  it("renders user-facing load failure without internal traceback", async () => {
    mockedFetchPlans.mockRejectedValue(new Error("Traceback: sqlite3.OperationalError"));

    const html = renderToStaticMarkup(await JournalPage());

    expect(html).toContain("Journal could not be loaded");
    expect(html).toContain("Check runtime status");
    expect(html).not.toContain("Traceback");
    expect(html).not.toContain("sqlite3.OperationalError");
  });
});
