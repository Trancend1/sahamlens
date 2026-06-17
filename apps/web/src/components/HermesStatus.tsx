"use client";

import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import type { HermesStatus as HermesStatusData, ControlResult } from "@/lib/hermes";

type ProcessDisplay = "running" | "stopped" | "disabled";

const PROCESS_COLORS: Record<ProcessDisplay, { bg: string; text: string }> = {
  running: { bg: "bg-emerald-500/10 border-emerald-500/30", text: "text-emerald-200" },
  stopped: { bg: "bg-amber-500/10 border-amber-500/30", text: "text-amber-200" },
  disabled: { bg: "bg-red-500/10 border-red-500/30", text: "text-red-200" },
};

const BADGE_OK = "rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] uppercase tracking-widest text-emerald-200";
const BADGE_NO = "rounded border border-red-500/30 bg-red-500/10 px-2 py-0.5 text-[10px] uppercase tracking-widest text-red-200";
const BADGE_AMBER = "rounded border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] uppercase tracking-widest text-amber-200";

export function HermesStatus() {
  const [status, setStatus] = useState<HermesStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/hermes/status");
      if (!res.ok) throw new Error("Failed to fetch status");
      const data: HermesStatusData = await res.json();
      setStatus(data);
    } catch {
      // ignore polling errors
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleAction = async (action: "start" | "stop") => {
    setActionLoading(true);
    try {
      const res = await fetch("/api/hermes/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const result: ControlResult = await res.json();
      if (result.ok) {
        toast.success(result.message);
        await fetchStatus();
      } else {
        toast.error(result.message);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Request failed");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div className="text-sm text-muted">Loading Hermes status...</div>;
  }

  if (!status) {
    return <div className="text-sm text-red-400">Failed to load Hermes status.</div>;
  }

  const processDisplay: ProcessDisplay = !status.config.enabled ? "disabled" : status.process.running ? "running" : "stopped";
  const colors = PROCESS_COLORS[processDisplay];
  const showStart = status.config.enabled && !status.process.running;
  const showStop = status.config.enabled && status.process.running;

  return (
    <div className="flex flex-col gap-4">
      <div className={`rounded-md border p-4 ${colors.bg}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`text-lg font-semibold capitalize ${colors.text}`}>{processDisplay}</p>
            {status.process.pid && (
              <p className="text-xs text-muted">PID: {status.process.pid}</p>
            )}
          </div>
          <div className="flex gap-2">
            {showStart && (
              <button
                onClick={() => handleAction("start")}
                disabled={actionLoading}
                className="rounded-md bg-emerald-600 px-4 py-2 text-xs font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                {actionLoading ? "Starting..." : "Start"}
              </button>
            )}
            {showStop && (
              <button
                onClick={() => handleAction("stop")}
                disabled={actionLoading}
                className="rounded-md bg-red-600 px-4 py-2 text-xs font-medium text-white hover:bg-red-500 disabled:opacity-50"
              >
                {actionLoading ? "Stopping..." : "Stop"}
              </button>
            )}
          </div>
        </div>
      </div>

      <section>
        <h2 className="mb-2 text-xs uppercase tracking-widest text-muted">Configuration</h2>
        <div className="grid gap-2">
          <div className="flex items-center justify-between rounded-md border border-muted/30 bg-white/[0.02] px-4 py-3">
            <span className="text-sm">Hermes Runtime</span>
            <span className={status.config.enabled ? BADGE_OK : BADGE_NO}>
              {status.config.enabled ? "Enabled" : "Disabled"}
            </span>
          </div>
          <div className="flex items-center justify-between rounded-md border border-muted/30 bg-white/[0.02] px-4 py-3">
            <span className="text-sm">Telegram</span>
            <span className={status.config.telegramConfigured ? BADGE_OK : BADGE_NO}>
              {status.config.telegramConfigured ? "Configured" : "Not configured"}
            </span>
          </div>
          <div className="flex items-center justify-between rounded-md border border-muted/30 bg-white/[0.02] px-4 py-3">
            <span className="text-sm">LLM Provider</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted">{status.config.providerName}</span>
              <span className={status.config.providerConfigured ? BADGE_OK : BADGE_AMBER}>
                {status.config.providerConfigured ? "Key set" : "No key"}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
