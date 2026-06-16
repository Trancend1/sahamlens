export type OverallStatus = "healthy" | "degraded" | "unhealthy";

export interface ComponentCheck {
  status: "ok" | "degraded" | "fail";
  label: string;
  detail: string;
}

export interface HealthReport {
  overall: OverallStatus;
  summary: string;
  checks: {
    python: ComponentCheck;
    database: ComponentCheck;
    runtime: ComponentCheck;
    llm: ComponentCheck;
  };
  refresh_mode: "manual";
}
