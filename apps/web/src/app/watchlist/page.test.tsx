import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fetchWatchlist } from "@/lib/watchlist";
import WatchlistPage from "./page";

vi.mock("@/lib/watchlist", () => ({
  fetchWatchlist: vi.fn(),
}));

const mockedFetchWatchlist = vi.mocked(fetchWatchlist);

describe("WatchlistPage", () => {
  beforeEach(() => {
    mockedFetchWatchlist.mockReset();
  });

  it("renders actionable empty state for an empty watchlist", async () => {
    mockedFetchWatchlist.mockResolvedValue([]);

    const html = renderToStaticMarkup(await WatchlistPage());

    expect(html).toContain("No tickers in your watchlist yet");
    expect(html).toContain("Import Portfolio");
    expect(html).not.toContain("scripts.watchlist");
    expect(html).not.toContain("Traceback");
  });

  it("renders user-facing load failure without internal traceback", async () => {
    mockedFetchWatchlist.mockRejectedValue(new Error("Traceback: no such table watchlist"));

    const html = renderToStaticMarkup(await WatchlistPage());

    expect(html).toContain("Watchlist could not be loaded");
    expect(html).toContain("Check runtime status");
    expect(html).not.toContain("Traceback");
    expect(html).not.toContain("no such table");
  });
});
