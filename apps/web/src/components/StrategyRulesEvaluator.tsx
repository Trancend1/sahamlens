"use client";

import { OperationButton } from "@/components/ui/OperationButton";

export function StrategyRulesEvaluator() {
  return (
    <OperationButton
      label="Evaluate Rules Now"
      runningLabel="Evaluating rules..."
      action={() =>
        fetch("/api/strategy-rules/evaluate", { method: "POST" }).then(
          (r) => r.json() as Promise<{ ok: boolean; message?: string; error?: string }>,
        )
      }
      reloadOnComplete
    />
  );
}
