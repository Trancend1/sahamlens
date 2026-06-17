import { NextRequest, NextResponse } from "next/server";
import { PythonRunnerError } from "@/lib/pythonRunner";
import { runCli } from "@/lib/cliCommands";

interface RouteParams {
  params: Promise<{ symbol: string }>;
}

export async function POST(_req: NextRequest, { params }: RouteParams): Promise<NextResponse> {
  const { symbol } = await params;
  try {
    await runCli("prices.refresh", { symbol, days: 365 });
    try {
      await runCli("indicators.calculate", { symbol });
    } catch {
      // indicators are best-effort
    }
    return NextResponse.json({ ok: true, message: `Prices refreshed for ${symbol}` });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
