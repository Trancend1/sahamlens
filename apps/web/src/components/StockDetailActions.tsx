"use client";

import { OperationButton } from "@/components/ui/OperationButton";

interface Props {
  symbol: string;
}

export function StockDetailActions({ symbol }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      <OperationButton
        label="Refresh Prices"
        runningLabel="Fetching prices..."
        action={() =>
          fetch(`/api/stocks/${encodeURIComponent(symbol)}/refresh-prices`, { method: "POST" }).then(
            (r) => r.json() as Promise<{ ok: boolean; message?: string; error?: string }>,
          )
        }
        reloadOnComplete
      />
      <OperationButton
        label="Refresh Fundamentals"
        runningLabel="Fetching fundamentals..."
        action={() =>
          fetch(`/api/stocks/${encodeURIComponent(symbol)}/refresh-fundamentals`, {
            method: "POST",
          }).then(
            (r) => r.json() as Promise<{ ok: boolean; message?: string; error?: string }>,
          )
        }
        reloadOnComplete
      />
      <OperationButton
        label="Fetch & Summarize News"
        runningLabel="Fetching news..."
        action={() =>
          fetch(`/api/stocks/${encodeURIComponent(symbol)}/fetch-news`, { method: "POST" }).then(
            (r) => r.json() as Promise<{ ok: boolean; message?: string; error?: string }>,
          )
        }
        reloadOnComplete
      />
    </div>
  );
}
