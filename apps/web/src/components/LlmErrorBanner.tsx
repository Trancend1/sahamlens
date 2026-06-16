"use client";

import { useEffect, useState } from "react";
import type { LlmStatus } from "@/app/api/llm/status/route";

interface Props {
  featureLabel?: string;
}

export function LlmErrorBanner({ featureLabel = "This AI feature" }: Props) {
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
        if (!cancelled) setStatus(null);
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
  if (status?.configured) return null;

  return (
    <div className="rounded border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      <p className="font-medium">LLM provider not configured</p>
      <p className="mt-1">
        {featureLabel} requires an LLM provider (API key).{" "}
        {status?.error && (
          <span className="text-amber-600">{status.error}. </span>
        )}
      </p>
      <p className="mt-1 text-xs text-amber-600">
        Set up your provider in{" "}
        <code className="rounded bg-amber-100 px-1">.env.local</code>:
      </p>
      <pre className="mt-1 overflow-x-auto rounded bg-amber-100/50 p-2 text-xs">
        SAHAMLENS_LLM_PROVIDER=openrouter{"\n"}
        SAHAMLENS_LLM_API_KEY=sk-or-...{"\n"}
        SAHAMLENS_LLM_BASE_URL=https://openrouter.ai/api/v1{"\n"}
        SAHAMLENS_LLM_MODEL=anthropic/claude-sonnet-4-6
      </pre>
    </div>
  );
}
