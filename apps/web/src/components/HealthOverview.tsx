"use client";

import type { HealthReport, OverallStatus } from "@/lib/health";

const OVERALL_COLORS: Record<OverallStatus, { icon: string; bg: string; text: string }> = {
  healthy: { icon: "\u{1F7E2}", bg: "border-emerald-500/30 bg-emerald-500/10", text: "text-emerald-200" },
  degraded: { icon: "\u{1F7E1}", bg: "border-amber-500/30 bg-amber-500/10", text: "text-amber-200" },
  unhealthy: { icon: "\u{1F534}", bg: "border-red-500/30 bg-red-500/10", text: "text-red-200" },
};

const CHECK_COLORS: Record<string, string> = {
  ok: "text-emerald-400",
  degraded: "text-amber-400",
  fail: "text-red-400",
};

interface Props {
  report: HealthReport;
}

export function HealthOverview({ report }: Props) {
  const colors = OVERALL_COLORS[report.overall];

  return (
    <div className="flex flex-col gap-6">
      <div className={`rounded-md border p-5 ${colors.bg}`}>
        <div className="flex items-center gap-3">
          <span className="text-2xl">{colors.icon}</span>
          <div>
            <p className={`text-lg font-semibold capitalize ${colors.text}`}>
              {report.overall}
            </p>
            <p className="text-sm text-muted">{report.summary}</p>
          </div>
        </div>
      </div>

      <section>
        <h2 className="mb-3 text-xs uppercase tracking-widest text-muted">System Health</h2>
        <div className="grid gap-2">
          {Object.values(report.checks).map((check) => (
            <div
              key={check.label}
              className="flex items-center justify-between rounded-md border border-muted/30 bg-white/[0.02] px-4 py-3"
            >
              <span className="text-sm">{check.label}</span>
              <span className={`text-sm font-medium ${CHECK_COLORS[check.status] ?? "text-muted"}`}>
                {check.detail}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-xs uppercase tracking-widest text-muted">Data Refresh</h2>
        <div className="rounded-md border border-muted/30 bg-white/[0.02] px-4 py-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">Mode</span>
            <span className="rounded border border-muted/40 px-2 py-0.5 text-[10px] uppercase tracking-widest text-muted">
              {report.refresh_mode}
            </span>
          </div>
          <p className="mt-2 text-xs text-muted">
            Refresh occurs through provider actions and stale-data banners. Automatic scheduling is planned.
          </p>
        </div>
      </section>

      <details className="rounded-md border border-muted/30 bg-white/[0.02]">
        <summary className="cursor-pointer px-4 py-2 text-xs font-medium text-muted hover:text-fg">
          View Full Health JSON
        </summary>
        <pre className="overflow-x-auto px-4 pb-3 pt-1 text-xs text-muted">
          {JSON.stringify(report, null, 2)}
        </pre>
      </details>
    </div>
  );
}
