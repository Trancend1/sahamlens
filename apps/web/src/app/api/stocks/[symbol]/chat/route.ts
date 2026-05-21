import { NextRequest, NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";
import type { ChatResponse } from "@/lib/stockBrief";

interface RouteParams {
  params: Promise<{ symbol: string }>;
}

export async function POST(req: NextRequest, { params }: RouteParams): Promise<NextResponse> {
  const { symbol } = await params;
  let question: string;
  try {
    const body = (await req.json()) as { question?: unknown };
    if (typeof body.question !== "string" || !body.question.trim()) {
      return NextResponse.json({ error: "question required" }, { status: 400 });
    }
    question = body.question.trim();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  try {
    const { data } = await runPython<ChatResponse>("scripts.generate_brief", {
      args: ["chat", "--symbol", symbol, "--question", question],
      timeoutMs: 60_000,
    });
    return NextResponse.json(data);
  } catch (err) {
    if (err instanceof PythonRunnerError) {
      const code = err.exitCode;
      if (code === 3) {
        return NextResponse.json(
          { error: "AI chat tidak tersedia saat ini." },
          { status: 503 },
        );
      }
      return NextResponse.json({ error: err.message }, { status: 422 });
    }
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
