import { NextRequest, NextResponse } from "next/server";
import { runPython, PythonRunnerError } from "@/lib/pythonRunner";
import type { TradePlan } from "@/lib/journal";

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid JSON body" }, { status: 400 });
  }

  try {
    const { data } = await runPython<TradePlan>("scripts.journal", {
      args: ["plan", "add", "--json", JSON.stringify(body)],
      timeoutMs: 15_000,
    });
    return NextResponse.json(data);
  } catch (err) {
    if (err instanceof PythonRunnerError) {
      return NextResponse.json(
        { error: "Trade plan could not be saved.", detail: "Check runtime readiness and try again." },
        { status: 422 },
      );
    }
    return NextResponse.json({ error: "Trade plan could not be saved." }, { status: 500 });
  }
}
