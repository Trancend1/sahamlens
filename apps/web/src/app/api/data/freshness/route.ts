import { NextResponse } from "next/server";
import { PythonRunnerError } from "@/lib/pythonRunner";
import { runCli } from "@/lib/cliCommands";

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
    const { data } = await runCli("freshness.check");
    return NextResponse.json(data as FreshnessReport);
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
    const { data } = await runCli("freshness.refresh");
    const result = (data ?? { ok: true, refreshed: [], errors: [] }) as {
      ok: boolean;
      refreshed: string[];
      errors: string[];
    };
    return NextResponse.json({
      ok: result.ok,
      message: `Refreshed: ${result.refreshed.join(", ") || "none"}`,
      refreshed: result.refreshed,
      errors: result.errors,
    });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
