import { NextRequest, NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";

interface RouteParams {
  params: Promise<{ symbol: string }>;
}

export async function POST(_req: NextRequest, { params }: RouteParams): Promise<NextResponse> {
  const { symbol } = await params;
  try {
    await runPython("scripts.ingest_news", {
      args: ["--symbols", symbol],
      timeoutMs: 120_000,
    });
    try {
      await runPython("scripts.summarize_news", {
        args: ["--symbol", symbol],
        timeoutMs: 60_000,
      });
    } catch {
      // summarization is best-effort
    }
    return NextResponse.json({ ok: true, message: `News fetched for ${symbol}` });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
