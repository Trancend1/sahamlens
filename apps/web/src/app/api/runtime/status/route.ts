import { fetchRuntimeStatus } from "@/lib/runtime";
import { runPython } from "@/lib/pythonRunner";

export interface InitStatus {
  schema_status: string;
  is_first_run: boolean;
  watchlist_count: number;
  ok: boolean;
}

export async function GET() {
  try {
    const status = await fetchRuntimeStatus();
    let watchlistCount = 0;
    try {
      const { data } = await runPython<unknown[]>("scripts.watchlist", {
        args: ["--json", "list"],
        timeoutMs: 10_000,
      });
      watchlistCount = Array.isArray(data) ? data.length : 0;
    } catch {
      // watchlist read is non-critical
    }
    const isFirstRun = status.schema_status === "ready" && watchlistCount === 0;
    return Response.json({
      schema_status: status.schema_status,
      is_first_run: isFirstRun,
      watchlist_count: watchlistCount,
      ok: status.ok,
    } satisfies InitStatus);
  } catch {
    return Response.json({
      schema_status: "unknown",
      is_first_run: false,
      watchlist_count: 0,
      ok: false,
    } satisfies InitStatus);
  }
}
