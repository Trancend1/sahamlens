"use client";

import { OperationButton } from "@/components/ui/OperationButton";

export function ProviderHealthRefresh() {
  return (
    <OperationButton
      label="Check Provider Health Now"
      runningLabel="Refreshing..."
      action={() =>
        fetch("/api/data-quality/refresh", { method: "POST" }).then(
          (r) => r.json() as Promise<{ ok: boolean; message?: string; error?: string }>,
        )
      }
      reloadOnComplete
    />
  );
}
