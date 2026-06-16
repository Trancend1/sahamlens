import { NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";

export async function POST(): Promise<NextResponse> {
  try {
    await runPython("scripts.journal_review", {
      args: ["review", "generate", "--json"],
      timeoutMs: 120_000,
    });
    return NextResponse.json({ ok: true, message: "Weekly review generated" });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
