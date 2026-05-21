import { NextRequest, NextResponse } from "next/server";
import { runPython, PythonRunnerError } from "@/lib/pythonRunner";
import type { JournalCritique } from "@/lib/journal";

export async function POST(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const planId = parseInt(id, 10);
  if (isNaN(planId)) {
    return NextResponse.json({ error: "invalid plan id" }, { status: 400 });
  }

  try {
    const { data } = await runPython<JournalCritique>("scripts.journal", {
      args: ["plan", "critique", "--id", String(planId)],
      timeoutMs: 60_000,
    });
    return NextResponse.json(data);
  } catch (err) {
    if (err instanceof PythonRunnerError) {
      const exitCode = err.exitCode;
      if (exitCode === 3) {
        return NextResponse.json(
          { error: "critique unavailable (budget exceeded or provider error)" },
          { status: 503 },
        );
      }
      if (exitCode === 2) {
        return NextResponse.json({ error: "plan not found" }, { status: 404 });
      }
      return NextResponse.json(
        { error: "critique failed", detail: err.stderr },
        { status: 422 },
      );
    }
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
