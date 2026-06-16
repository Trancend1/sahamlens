import { NextRequest, NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";

interface RouteParams {
  params: Promise<{ symbol: string }>;
}

export async function POST(_req: NextRequest, { params }: RouteParams): Promise<NextResponse> {
  const { symbol } = await params;
  try {
    await runPython("scripts.ingest_prices", {
      args: ["--symbols", symbol, "--days", "365"],
      timeoutMs: 120_000,
    });
    try {
      await runPython("scripts.calculate_indicators", {
        args: ["--symbols", symbol],
        timeoutMs: 60_000,
      });
    } catch {
      // indicators are best-effort
    }
    return NextResponse.json({ ok: true, message: `Prices refreshed for ${symbol}` });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
