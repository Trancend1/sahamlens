import { NextResponse } from "next/server";
import { PythonRunnerError } from "@/lib/pythonRunner";
import { runCli } from "@/lib/cliCommands";

export async function POST(): Promise<NextResponse> {
  try {
    await runCli("weekly_review.generate");
    return NextResponse.json({ ok: true, message: "Weekly review generated" });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
