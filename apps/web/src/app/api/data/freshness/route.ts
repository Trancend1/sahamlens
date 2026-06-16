import { NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";

export interface FreshnessRecord {
  data_type: string;
  status: string;
  last_refreshed_at: string | null;
  age_seconds: number | null;
  threshold_seconds: number;
}

export interface FreshnessReport {
  fresh_count: number;
  stale_count: number;
  total_count: number;
  has_stale: boolean;
  stale_types: string[];
  records: FreshnessRecord[];
}

export async function GET(): Promise<NextResponse> {
  try {
    const { data } = await runPython<FreshnessReport>("scripts.freshness", {
      args: ["check", "--json"],
      timeoutMs: 15_000,
    });
    return NextResponse.json(data);
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json(
      {
        ok: false,
        error: msg,
        fresh_count: 0,
        stale_count: 0,
        total_count: 0,
        has_stale: false,
        stale_types: [],
        records: [],
      },
      { status: 500 },
    );
  }
}

export async function POST(): Promise<NextResponse> {
  try {
    const { data } = await runPython<{ ok: boolean; refreshed: string[]; errors: string[] }>(
      "scripts.freshness",
      { args: ["refresh", "--json"], timeoutMs: 300_000 },
    );
    return NextResponse.json({ ok: data.ok, message: `Refreshed: ${data.refreshed.join(", ") || "none"}`, refreshed: data.refreshed, errors: data.errors });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
