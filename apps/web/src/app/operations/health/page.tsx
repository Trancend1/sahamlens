import { runPython } from "@/lib/pythonRunner";
import type { RuntimeStatus } from "@/lib/runtime";
import type { HealthReport, ComponentCheck, OverallStatus } from "@/lib/health";
import { HealthOverview } from "@/components/HealthOverview";

export const dynamic = "force-dynamic";

function makeCheck(status: "ok" | "degraded" | "fail", label: string, detail: string): ComponentCheck {
  return { status, label, detail };
}

function computeOverall(checks: HealthReport["checks"]): { overall: OverallStatus; summary: string } {
  const statuses = Object.values(checks).map((c) => c.status);
  if (statuses.some((s) => s === "fail")) return { overall: "unhealthy", summary: "Core services unavailable." };
  if (statuses.some((s) => s === "degraded")) return { overall: "degraded", summary: "Some non-critical services unavailable." };
  return { overall: "healthy", summary: "All required services available." };
}

export default async function HealthPage() {
  type CheckStatus = "ok" | "degraded" | "fail";
  let runtime: { status: CheckStatus; python: CheckStatus; database: CheckStatus } = {
    status: "fail",
    python: "fail",
    database: "fail",
  };
  let llmStatus: "ok" | "degraded" = "degraded";
  let llmDetail = "Could not check";

  try {
    const { data } = await runPython<RuntimeStatus>("scripts.runtime", {
      args: ["status", "--json"], timeoutMs: 30_000,
    });
    runtime = {
      status: data.schema_status === "ready" ? "ok" : "degraded",
      python: data.python_executable ? "ok" : "degraded",
      database: data.db_path ? "ok" : "fail",
    };
  } catch {
    // defaults to fail
  }

  try {
    const { data } = await runPython<{ ok: boolean; configured: boolean; provider: string; model: string }>(
      "scripts.llm_status", { args: ["--json"], timeoutMs: 15_000 },
    );
    if (data.configured) {
      llmStatus = "ok";
      llmDetail = `${data.provider} / ${data.model}`;
    } else {
      llmDetail = "Not configured";
    }
  } catch {
    llmDetail = "Could not verify";
  }

  const checks: HealthReport["checks"] = {
    python: makeCheck(runtime.python, "Core Engine", runtime.python === "ok" ? "Available" : "Unavailable"),
    database: makeCheck(runtime.database, "Database", runtime.database === "ok" ? "Ready" : "Not connected"),
    runtime: makeCheck(runtime.status, "Runtime", runtime.status === "ok" ? "Schema ready" : "Needs attention"),
    llm: makeCheck(llmStatus, "LLM Provider", llmDetail),
  };

  const { overall, summary } = computeOverall(checks);

  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted">
        System health overview. Check if all services are running correctly.
      </p>
      <HealthOverview report={{ overall, summary, checks, refresh_mode: "manual" }} />
    </div>
  );
}
