import { NextRequest, NextResponse } from "next/server";
import { PythonRunnerError } from "@/lib/pythonRunner";
import { runCli } from "@/lib/cliCommands";

interface RouteParams {
  params: Promise<{ symbol: string }>;
}

export async function POST(_req: NextRequest, { params }: RouteParams): Promise<NextResponse> {
  const { symbol } = await params;
  try {
    // ingest_news pulls all configured RSS feeds (no per-symbol filter upstream).
    await runCli("news.ingest");
    try {
      await runCli("news.summarize");
    } catch {
      // summarization is best-effort
    }
    return NextResponse.json({ ok: true, message: `News fetched for ${symbol}` });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
