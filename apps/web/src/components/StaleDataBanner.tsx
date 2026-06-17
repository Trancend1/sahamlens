"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import type { FreshnessReport } from "@/app/api/data/freshness/route";

const POLL_INTERVAL = 5 * 60 * 1000;

export function StaleDataBanner(): React.ReactElement | null {
  const [report, setReport] = useState<FreshnessReport | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchFreshness = useCallback(async () => {
    try {
      const res = await fetch("/api/data/freshness");
      if (!res.ok) return;
      const data: FreshnessReport = await res.json();
      setReport(data);
    } catch {
      /* silent */
    }
  }, []);

  useEffect(() => {
    fetchFreshness();
    const id = setInterval(fetchFreshness, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [fetchFreshness]);

  const handleRefreshAll = useCallback(async () => {
    setRefreshing(true);
    try {
      const res = await fetch("/api/data/freshness", { method: "POST" });
      const result = await res.json();
      if (res.ok && result.ok) {
        toast.success(result.message ?? "Semua data stale berhasil di-refresh");
        setDismissed(true);
        await fetchFreshness();
      } else {
        toast.error(result.error ?? "Gagal refresh data stale");
      }
    } catch {
      toast.error("Gagal menghubungi server");
    } finally {
      setRefreshing(false);
    }
  }, [fetchFreshness]);

  if (!report || !report.has_stale || dismissed) return null;

  return (
    <div className="flex items-center gap-3 border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">
      <span className="inline-block size-2 shrink-0 rounded-full bg-amber-400" />
      <span className="flex-1">
        {report.stale_count} jenis data sudah stale: {report.stale_types.join(", ")}
      </span>
      <button
        type="button"
        onClick={handleRefreshAll}
        disabled={refreshing}
        className="rounded border border-amber-500/40 px-2.5 py-1 text-xs font-medium text-amber-200 transition-colors hover:bg-amber-500/20 disabled:opacity-50"
      >
        {refreshing ? "Refreshing..." : "Refresh All"}
      </button>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="text-xs text-amber-300/60 hover:text-amber-200"
        aria-label="Tutup"
      >
        ✕
      </button>
    </div>
  );
}
