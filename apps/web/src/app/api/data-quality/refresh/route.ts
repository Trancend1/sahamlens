import { NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";

export async function POST(): Promise<NextResponse> {
  try {
    await runPython("scripts.provider_health", {
      args: ["refresh", "--json"],
      timeoutMs: 120_000,
    });
    return NextResponse.json({ ok: true, message: "Provider health refreshed" });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
