"use client";

import { useState } from "react";
import type { EvidenceItem, StockBrief } from "@/lib/stockBrief";
import { LlmErrorBanner } from "@/components/LlmErrorBanner";

interface Props {
  symbol: string;
}

const EVIDENCE_LABELS: Record<EvidenceItem["type"], string> = {
  price: "Price",
  indicator: "Indicator",
  news: "News",
  fundamental: "Fundamental",
  journal: "Journal",
};

export function StockBriefPanel({ symbol }: Props) {
  const [brief, setBrief] = useState<StockBrief | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/stocks/${symbol}/brief`, { method: "POST" });
      if (!res.ok) {
        const body = (await res.json()) as { error?: string };
        setError(body.error ?? "The AI brief could not be generated.");
        return;
      }
      setBrief((await res.json()) as StockBrief);
    } catch {
      setError("The AI brief could not be generated.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted">
          AI Brief
        </h2>
        {!brief ? (
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="rounded border border-accent/40 px-3 py-1 text-xs text-accent hover:bg-accent/10 disabled:opacity-50"
            type="button"
          >
            {loading ? "Generating..." : "Generate brief"}
          </button>
        ) : null}
        {brief ? (
          <button
            onClick={() => {
              setBrief(null);
            }}
            className="text-xs text-muted hover:text-accent"
            type="button"
          >
            Refresh brief
          </button>
        ) : null}
      </div>

      {error ? (
        <p className="rounded border border-red-500/40 bg-red-500/[0.05] p-3 text-xs text-red-300">
          {error}
        </p>
      ) : null}

      <LlmErrorBanner featureLabel="AI Brief" />

      {!brief && !loading && !error ? (
        <p className="text-xs text-muted">
          Generate a brief from available local data, then review evidence and caveats manually.
        </p>
      ) : null}

      {loading ? (
        <p className="animate-pulse text-xs text-muted">Generating local-data brief...</p>
      ) : null}

      {brief ? (
        <div className="flex flex-col gap-4">
          <div className="grid gap-3 md:grid-cols-2">
            <ViewBlock label="Bullish context" text={brief.bullish_view} color="green" />
            <ViewBlock label="Bearish context" text={brief.bearish_view} color="red" />
          </div>

          <ViewBlock label="Uncertainty" text={brief.uncertainty} color="yellow" />

          <div className="rounded border border-muted/20 bg-white/[0.02] p-3">
            <p className="mb-1 text-xs font-medium text-muted">Beginner explanation</p>
            <p className="text-sm">{brief.beginner_explanation}</p>
          </div>

          <div className="rounded border border-muted/20 bg-white/[0.02] p-3">
            <p className="mb-2 text-xs font-medium text-muted">
              Evidence ({brief.evidence.length})
            </p>
            <ul className="flex flex-col gap-1">
              {brief.evidence.map((evidence, index) => (
                <li key={`${evidence.type}-${index}`} className="flex gap-2 text-xs">
                  <span className="shrink-0 rounded bg-accent/10 px-1.5 py-0.5 text-accent">
                    {EVIDENCE_LABELS[evidence.type]}
                  </span>
                  <span className="text-muted">{evidence.value}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded border border-yellow-500/20 bg-yellow-500/[0.03] p-3">
            <p className="mb-1 text-xs font-medium text-yellow-400">Caveats</p>
            <ul className="list-disc pl-4 text-xs text-muted">
              {brief.caveats.map((caveat, index) => (
                <li key={`${caveat}-${index}`}>{caveat}</li>
              ))}
            </ul>
          </div>

          {brief.suggested_next_question ? (
            <p className="text-xs text-muted">
              <span className="font-medium text-accent">Suggested follow-up:</span>{" "}
              {brief.suggested_next_question}
            </p>
          ) : null}

          <p className="text-xs text-muted/60">
            Not financial advice. AI explains; you decide. Model: {brief.model} / {brief.analysis_date}
          </p>
        </div>
      ) : null}
    </section>
  );
}

function ViewBlock({
  label,
  text,
  color,
}: {
  label: string;
  text: string;
  color: "green" | "red" | "yellow";
}) {
  const styles = {
    green: "border-green-500/20 bg-green-500/[0.03]",
    red: "border-red-500/20 bg-red-500/[0.03]",
    yellow: "border-yellow-500/20 bg-yellow-500/[0.03]",
  };
  const labelStyles = {
    green: "text-green-400",
    red: "text-red-400",
    yellow: "text-yellow-400",
  };
  return (
    <div className={`rounded border p-3 ${styles[color]}`}>
      <p className={`mb-1 text-xs font-medium ${labelStyles[color]}`}>{label}</p>
      <p className="text-sm">{text}</p>
    </div>
  );
}
