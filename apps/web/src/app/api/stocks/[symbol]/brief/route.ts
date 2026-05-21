import { NextRequest, NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";
import type { StockBrief } from "@/lib/stockBrief";

interface RouteParams {
  params: Promise<{ symbol: string }>;
}

export async function POST(_req: NextRequest, { params }: RouteParams): Promise<NextResponse> {
  const { symbol } = await params;
  try {
    const { data } = await runPython<StockBrief>("scripts.generate_brief", {
      args: ["brief", "--symbol", symbol],
      timeoutMs: 60_000,
    });
    return NextResponse.json(data);
  } catch (err) {
    if (err instanceof PythonRunnerError) {
      const code = err.exitCode;
      if (code === 3) {
        return NextResponse.json(
          { error: "AI brief tidak tersedia saat ini." },
          { status: 503 },
        );
      }
      return NextResponse.json({ error: err.message }, { status: 422 });
    }
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
