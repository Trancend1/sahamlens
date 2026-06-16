"use client";

import { useEffect, useState } from "react";
import type { LlmStatus } from "@/app/api/llm/status/route";

interface Props {
  compact?: boolean;
}

export function LlmStatusBadge({ compact = false }: Props) {
  const [status, setStatus] = useState<LlmStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchStatus() {
      try {
        const res = await fetch("/api/llm/status");
        const data = (await res.json()) as LlmStatus;
        if (!cancelled) setStatus(data);
      } catch {
        if (!cancelled)
          setStatus({
            configured: false,
            provider: "unknown",
            model: "",
            error: "Failed to check LLM configuration",
          });
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchStatus();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return null;

  if (compact) {
    return status?.configured ? (
      <span className="inline-flex items-center gap-1 text-xs text-green-600">
        <span className="size-1.5 rounded-full bg-green-500" />
        {status.provider}
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 text-xs text-amber-600">
        <span className="size-1.5 rounded-full bg-amber-500" />
        LLM not configured
      </span>
    );
  }

  if (status?.configured) {
    return (
      <div className="rounded border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
        <span className="font-medium">LLM:</span>{" "}
        {status.provider} ({status.model}){" "}
        <span className="text-green-600">✓ configured</span>
      </div>
    );
  }

  return (
    <div className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
      <span className="font-medium">LLM provider not configured</span>
      {status?.error && (
        <p className="mt-1 text-xs text-amber-600">{status.error}</p>
      )}
      <p className="mt-1 text-xs text-amber-600">
        AI features (brief, chat, critique, news summary) will not work.
        Set <code className="rounded bg-amber-100 px-1">SAHAMLENS_LLM_API_KEY</code>{" "}
        in <code className="rounded bg-amber-100 px-1">.env.local</code>.
      </p>
    </div>
  );
}
