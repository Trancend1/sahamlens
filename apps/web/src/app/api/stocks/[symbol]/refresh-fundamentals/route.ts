import { NextRequest, NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";

interface RouteParams {
  params: Promise<{ symbol: string }>;
}

export async function POST(_req: NextRequest, { params }: RouteParams): Promise<NextResponse> {
  const { symbol } = await params;
  try {
    await runPython("scripts.fundamentals", {
      args: ["coverage", "refresh", "--symbols", symbol],
      timeoutMs: 60_000,
    });
    return NextResponse.json({ ok: true, message: `Fundamentals refreshed for ${symbol}` });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
