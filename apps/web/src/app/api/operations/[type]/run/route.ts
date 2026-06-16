import { NextRequest, NextResponse } from "next/server";
import { runPython, PythonRunnerError } from "@/lib/pythonRunner";
import { getOperation } from "@/lib/operations";

interface ScriptMapping {
  module: string;
  args: string[];
}

const SCRIPT_MAP: Record<string, ScriptMapping> = {
  provider_health: { module: "scripts.provider_health", args: ["refresh", "--json"] },
  prices: { module: "scripts.ingest_prices", args: ["--from-watchlist", "--days", "7", "--json"] },
  fundamentals: { module: "scripts.fundamentals", args: ["coverage", "refresh", "--from-watchlist", "--json"] },
  news: { module: "scripts.ingest_news", args: ["--from-watchlist", "--json"] },
  alerts: { module: "scripts.alerts", args: ["evaluate", "--json"] },
  screener: { module: "scripts.screener", args: ["run", "--builtin", "fundamentals-basic", "--from-watchlist", "--json"] },
  strategy_rules: { module: "scripts.journal_review", args: ["rules", "evaluate", "--json"] },
  weekly_review: { module: "scripts.journal_review", args: ["review", "generate", "--json"] },
};

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ type: string }> }
): Promise<NextResponse> {
  const { type } = await params;

  if (!getOperation(type)) {
    return NextResponse.json({ ok: false, error: `Unknown operation: ${type}` }, { status: 400 });
  }

  const mapping = SCRIPT_MAP[type];
  if (!mapping) {
    return NextResponse.json({ ok: false, error: `No script mapping for: ${type}` }, { status: 500 });
  }

  try {
    const { data } = await runPython<{ ok: boolean }>(mapping.module, {
      args: mapping.args,
      timeoutMs: getOperation(type)?.timeoutMs ?? 120_000,
    });
    return NextResponse.json({ ok: data.ok ?? true, type });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg, type }, { status: 500 });
  }
}
