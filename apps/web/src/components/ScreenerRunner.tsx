"use client";

import { OperationButton } from "@/components/ui/OperationButton";

export function ScreenerRunner() {
  return (
    <OperationButton
      label="Run Screener Now"
      runningLabel="Running screener..."
      action={() =>
        fetch("/api/screener/run", { method: "POST" }).then(
          (r) => r.json() as Promise<{ ok: boolean; message?: string; error?: string }>,
        )
      }
      reloadOnComplete
      variant="primary"
    />
  );
}
