"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import { getOperationsByCategory } from "@/lib/operations";
import type { OperationCategory } from "@/lib/operations";
import type { FreshnessReport, FreshnessRecord } from "@/lib/runtime";
import { FreshnessBadge } from "@/components/FreshnessBadge";

interface Props {
  report: FreshnessReport;
}

function getRecord(report: FreshnessReport, key: string): FreshnessRecord | undefined {
  return report.records.find((r) => r.data_type === key);
}

function CategorySection({
  category,
  label,
  report,
}: {
  category: OperationCategory;
  label: string;
  report: FreshnessReport;
}) {
  const ops = getOperationsByCategory()[category];
  if (ops.length === 0) return null;

  return (
    <section>
      <h2 className="mb-3 text-xs uppercase tracking-widest text-muted">{label}</h2>
      <div className="grid gap-2">
        {ops.map((op) => {
          const record = getRecord(report, op.freshnessKey);
          return (
            <OperationRow key={op.id} operation={op} record={record} />
          );
        })}
      </div>
    </section>
  );
}

function OperationRow({
  operation,
  record,
}: {
  operation: { id: string; name: string; description: string; route: string };
  record: FreshnessRecord | undefined;
}) {
  const [running, setRunning] = useState(false);

  const handleRun = useCallback(async () => {
    setRunning(true);
    try {
      const res = await fetch(operation.route, { method: "POST" });
      const data = await res.json();
      if (res.ok && data.ok) {
        toast.success(`${operation.name} selesai`);
        window.location.reload();
      } else {
        toast.error(data.error ?? `${operation.name} gagal`);
      }
    } catch {
      toast.error(`Gagal menjalankan ${operation.name}`);
    } finally {
      setRunning(false);
    }
  }, [operation]);

  return (
    <div className="flex items-center justify-between rounded-md border border-muted/30 bg-white/[0.02] px-4 py-3">
      <div className="flex items-center gap-3">
        <div>
          <p className="text-sm font-medium">{operation.name}</p>
          <p className="text-xs text-muted">{operation.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {record?.last_refreshed_at ? (
          <FreshnessBadge iso={record.last_refreshed_at} />
        ) : (
          <span className="rounded border border-muted/40 px-2 py-0.5 text-[10px] uppercase tracking-widest text-muted">
            Never
          </span>
        )}
        <button
          type="button"
          onClick={handleRun}
          disabled={running}
          className="rounded border border-accent/40 px-2.5 py-1 text-xs font-medium text-accent transition-colors hover:bg-accent/10 disabled:opacity-50"
        >
          {running ? "Running..." : "Run Now"}
        </button>
      </div>
    </div>
  );
}

export function OperationsTable({ report }: Props) {
  const [refreshingAll, setRefreshingAll] = useState(false);

  const handleRefreshAll = useCallback(async () => {
    setRefreshingAll(true);
    try {
      const res = await fetch("/api/data/freshness", { method: "POST" });
      const data = await res.json();
      if (res.ok && data.ok) {
        toast.success(data.message ?? "Semua data stale berhasil di-refresh");
        window.location.reload();
      } else {
        toast.error(data.error ?? "Gagal refresh");
      }
    } catch {
      toast.error("Gagal menghubungi server");
    } finally {
      setRefreshingAll(false);
    }
  }, []);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div className="flex gap-4 text-sm">
          <span className="text-muted">
            Total: <strong className="text-fg">{report.total_count}</strong>
          </span>
          <span className="text-emerald-400">
            Fresh: <strong>{report.fresh_count}</strong>
          </span>
          <span className="text-amber-400">
            Stale: <strong>{report.stale_count}</strong>
          </span>
        </div>
        {report.has_stale && (
          <button
            type="button"
            onClick={handleRefreshAll}
            disabled={refreshingAll}
            className="rounded bg-accent px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-accent/80 disabled:opacity-50"
          >
            {refreshingAll ? "Refreshing..." : "Run All Stale"}
          </button>
        )}
      </div>

      <CategorySection category="provider" label="Providers" report={report} />
      <CategorySection category="analysis" label="Analysis" report={report} />
      <CategorySection category="review" label="Review" report={report} />
    </div>
  );
}
