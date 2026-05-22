import { runPython } from "./pythonRunner";

export interface WatchlistEntry {
  symbol: string;
  tag: string | null;
  note: string | null;
  added_at: string;
  fetched_at: string | null;
}

export async function fetchWatchlist(): Promise<WatchlistEntry[]> {
  const { data } = await runPython<WatchlistEntry[]>("scripts.watchlist", {
    args: ["--json", "list"],
  });
  return data;
}
