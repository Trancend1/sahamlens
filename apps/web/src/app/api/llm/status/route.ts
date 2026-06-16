import { NextResponse } from "next/server";
import { PythonRunnerError, runPython } from "@/lib/pythonRunner";

export interface LlmStatus {
  configured: boolean;
  provider: string;
  model: string;
  error: string | null;
}

export const dynamic = "force-dynamic";

export async function GET(): Promise<NextResponse> {
  try {
    const { data } = await runPython<LlmStatus>("scripts.llm_status", {
      timeoutMs: 15_000,
    });
    return NextResponse.json(data);
  } catch (err) {
    if (err instanceof PythonRunnerError) {
      return NextResponse.json(
        {
          configured: false,
          provider: "unknown",
          model: "",
          error: `Failed to check LLM status: ${err.message}`,
        },
        { status: 200 },
      );
    }
    return NextResponse.json(
      {
        configured: false,
        provider: "unknown",
        model: "",
        error: "Failed to check LLM status",
      },
      { status: 200 },
    );
  }
}
