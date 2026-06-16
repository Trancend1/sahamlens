"use client";

import { OperationButton } from "@/components/ui/OperationButton";

export function WeeklyReviewGenerator() {
  return (
    <OperationButton
      label="Generate Weekly Review"
      runningLabel="Generating review..."
      action={() =>
        fetch("/api/journal/generate-review", { method: "POST" }).then(
          (r) => r.json() as Promise<{ ok: boolean; message?: string; error?: string }>,
        )
      }
      reloadOnComplete
      variant="primary"
    />
  );
}
