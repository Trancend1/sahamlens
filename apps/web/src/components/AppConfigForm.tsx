"use client";

import { useEffect, useState } from "react";

interface AppConfig {
  dataDir: string;
}

export function AppConfigForm() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await fetch("/api/config?section=app");
        if (!res.ok) return;
        const { config: cfg } = await res.json() as { section: string; config: AppConfig };
        if (!cancelled) setConfig(cfg);
      } catch {
        // silent
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="flex flex-col gap-4 rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <h2 className="text-sm font-medium">Application Configuration</h2>
      <label className="grid gap-1">
        <span className="text-sm font-medium">Database Path</span>
        <input
          readOnly
          value={loading ? "Loading..." : (config?.dataDir ?? "Unknown")}
          className="rounded-md border border-muted/30 px-3 py-2 text-sm bg-black/30 text-muted cursor-not-allowed"
        />
      </label>
      <p className="text-xs text-muted">Database path is configured in the DuckDB connection string.</p>
    </div>
  );
}
