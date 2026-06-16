import { NextResponse } from "next/server";
import { runPython } from "@/lib/pythonRunner";
import type { RuntimeStatus } from "@/lib/runtime";
import type { OverallStatus, ComponentCheck, HealthReport } from "@/lib/health";

function makeCheck(status: "ok" | "degraded" | "fail", label: string, detail: string): ComponentCheck {
  return { status, label, detail };
}

async function checkRuntime(): Promise<{
  runtime: ComponentCheck;
  python: ComponentCheck;
  database: ComponentCheck;
}> {
  try {
    const { data } = await runPython<RuntimeStatus>("scripts.runtime", {
      args: ["status", "--json"],
      timeoutMs: 30_000,
    });
    const schemaReady = data.schema_status === "ready";
    return {
      runtime: makeCheck(schemaReady ? "ok" : "degraded", "Runtime", schemaReady ? "Schema ready" : `Schema: ${data.schema_status}`),
      python: makeCheck(data.python_executable ? "ok" : "degraded", "Core Engine", data.python_executable ?? "Not resolved"),
      database: makeCheck(data.db_path ? "ok" : "fail", "Database", data.db_path ? `Connected (${data.applied_migrations.length} migrations)` : "Not configured"),
    };
  } catch {
    return {
      runtime: makeCheck("fail", "Runtime", "Could not query runtime status"),
      python: makeCheck("fail", "Core Engine", "Python subprocess failed"),
      database: makeCheck("fail", "Database", "Could not connect to DuckDB"),
    };
  }
}

async function checkLlm(): Promise<ComponentCheck> {
  try {
    const { data } = await runPython<{
      ok: boolean; provider: string; model: string; configured: boolean; error?: string;
    }>("scripts.llm_status", { args: ["--json"], timeoutMs: 15_000 });
    if (data.configured) {
      return makeCheck("ok", "LLM Provider", `${data.provider} / ${data.model}`);
    }
    return makeCheck("degraded", "LLM Provider", data.error ?? "Not configured");
  } catch {
    return makeCheck("degraded", "LLM Provider", "Could not verify LLM status");
  }
}

function computeOverall(checks: HealthReport["checks"]): { overall: OverallStatus; summary: string } {
  const statuses = Object.values(checks).map((c) => c.status);
  if (statuses.some((s) => s === "fail")) return { overall: "unhealthy", summary: "Core services unavailable." };
  if (statuses.some((s) => s === "degraded")) return { overall: "degraded", summary: "Some non-critical services unavailable." };
  return { overall: "healthy", summary: "All required services available." };
}

export async function GET(): Promise<NextResponse> {
  const [runtimeChecks, llmCheck] = await Promise.all([
    checkRuntime(),
    checkLlm(),
  ]);

  const checks: HealthReport["checks"] = {
    python: runtimeChecks.python,
    database: runtimeChecks.database,
    runtime: runtimeChecks.runtime,
    llm: llmCheck,
  };

  const { overall, summary } = computeOverall(checks);

  return NextResponse.json({
    overall, summary, checks, refresh_mode: "manual",
  } satisfies HealthReport);
}
