import { NextResponse } from "next/server";
import { PythonRunnerError } from "@/lib/pythonRunner";
import { runCli } from "@/lib/cliCommands";

export async function POST(): Promise<NextResponse> {
  try {
    await runCli("strategy_rules.evaluate");
    return NextResponse.json({ ok: true, message: "Strategy rules evaluated" });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
