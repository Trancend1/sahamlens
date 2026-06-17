import { NextRequest, NextResponse } from "next/server";
import { PythonRunnerError } from "@/lib/pythonRunner";
import { getOperation } from "@/lib/operations";
import { runCli, OPERATION_CLI_MAP, type CliParams } from "@/lib/cliCommands";

// Provider/analysis refreshes that operate over the whole watchlist.
const WATCHLIST_PARAMS: CliParams = { fromWatchlist: true, days: 7 };

export async function POST(
  _req: NextRequest,
  { params }: { params: Promise<{ type: string }> }
): Promise<NextResponse> {
  const { type } = await params;
  const op = getOperation(type);

  if (!op) {
    return NextResponse.json({ ok: false, error: `Unknown operation: ${type}`, type }, { status: 400 });
  }

  const commandKey = OPERATION_CLI_MAP[type];
  if (!commandKey) {
    return NextResponse.json({ ok: false, error: `No CLI mapping for: ${type}`, type }, { status: 500 });
  }

  // Operations that accept a symbol source run against the watchlist here.
  const usesWatchlist = type === "prices" || type === "fundamentals" || type === "screener";

  try {
    await runCli(commandKey, usesWatchlist ? WATCHLIST_PARAMS : {});
    return NextResponse.json({ ok: true, type });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg, type }, { status: 500 });
  }
}
