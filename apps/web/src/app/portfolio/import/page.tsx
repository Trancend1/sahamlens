"use client";

import Link from "next/link";
import { useState } from "react";
import { DataTableWrapper } from "@/components/ui/DataTableWrapper";
import { RuntimeErrorState } from "@/components/ui/RuntimeErrorState";
import type { ImportResult, PortfolioPosition } from "@/lib/portfolio";

type ImportPhase = "upload" | "preview" | "mapping" | "saving" | "done" | "error";

export default function PortfolioImportPage() {
  const [phase, setPhase] = useState<ImportPhase>("upload");
  const [csvContent, setCsvContent] = useState("");
  const [result, setResult] = useState<ImportResult | null>(null);
  const [fieldMap, setFieldMap] = useState<Record<string, string>>({});
  const [errorMsg, setErrorMsg] = useState("");

  async function handleFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setCsvContent(text);
    await parseCSV(text, undefined);
  }

  async function parseCSV(csv: string, fieldMapOverride: Record<string, string> | undefined) {
    setErrorMsg("");
    try {
      const res = await fetch("/api/portfolio/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv_content: csv, field_map: fieldMapOverride }),
      });
      const data: ImportResult = await res.json();
      setResult(data);
      if (data.positions.length > 0) {
        setPhase("preview");
      } else {
        setFieldMap({
          symbol: data.detected_columns[0] ?? "",
          lots: data.detected_columns[1] ?? "",
          price: data.detected_columns[2] ?? "",
        });
        setPhase("mapping");
      }
    } catch {
      setErrorMsg("The CSV could not be parsed. Check the file format and try again.");
      setPhase("error");
    }
  }

  async function handleConfirm(positions: PortfolioPosition[]) {
    setPhase("saving");
    try {
      const res = await fetch("/api/portfolio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(positions),
      });
      if (!res.ok) {
        const body = (await res.json()) as { error?: string };
        setErrorMsg(body.error ?? "The portfolio positions could not be saved.");
        setPhase("error");
        return;
      }
      setPhase("done");
    } catch {
      setErrorMsg("The portfolio positions could not be saved. Check runtime readiness and try again.");
      setPhase("error");
    }
  }

  async function handleFieldMapSubmit() {
    await parseCSV(csvContent, fieldMap);
  }

  if (phase === "done") {
    return (
      <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
        <PageHeader />
        <div className="rounded-md border border-green-500/30 bg-green-500/5 px-5 py-4">
          <p className="text-sm font-medium text-green-400">Portfolio import completed</p>
          <p className="mt-1 text-xs text-muted">
            Review the imported positions before using them as portfolio context.
          </p>
        </div>
        <Link
          href="/portfolio"
          className="w-fit rounded border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10"
        >
          Open Portfolio
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <PageHeader />

      {phase === "upload" ? (
        <section className="rounded-md border border-muted/30 bg-white/[0.02] p-6">
          <label className="flex cursor-pointer flex-col items-center gap-3 text-sm text-muted hover:text-fg">
            <span className="text-2xl">Upload</span>
            <span>Choose a CSV file</span>
            <input type="file" accept=".csv,text/csv" onChange={handleFile} className="hidden" />
          </label>
        </section>
      ) : null}

      {result?.warnings && result.warnings.length > 0 ? (
        <section className="rounded-md border border-amber-500/40 bg-amber-500/[0.06] p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-amber-300">
            Import warnings
          </p>
          <ul className="mt-2 space-y-1 text-sm text-amber-200/80">
            {result.warnings.map((warning, index) => (
              <li key={`${warning}-${index}`}>{warning}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {phase === "mapping" && result ? (
        <section className="space-y-4 rounded-md border border-muted/30 bg-white/[0.02] p-5">
          <p className="text-sm font-medium">
            Columns were not detected automatically. Map the required fields below.
          </p>
          {(["symbol", "lots", "price"] as const).map((canonical) => (
            <div key={canonical}>
              <label className="mb-1 block text-xs uppercase tracking-widest text-muted">
                {canonical === "price" ? "Average buy price" : canonical}
              </label>
              <select
                value={fieldMap[canonical] ?? ""}
                onChange={(event) => setFieldMap((prev) => ({ ...prev, [canonical]: event.target.value }))}
                className="w-full rounded border border-muted/30 bg-transparent px-3 py-2 text-sm"
              >
                <option value="">Select column</option>
                {result.detected_columns.map((column) => (
                  <option key={column} value={column}>
                    {column}
                  </option>
                ))}
              </select>
            </div>
          ))}
          <button
            onClick={handleFieldMapSubmit}
            disabled={!fieldMap.symbol || !fieldMap.lots || !fieldMap.price}
            className="rounded border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10 disabled:opacity-40"
            type="button"
          >
            Process CSV
          </button>
        </section>
      ) : null}

      {phase === "preview" && result && result.positions.length > 0 ? (
        <section className="space-y-4">
          <p className="text-sm text-muted">
            {result.positions.length} position(s) detected. Confirming will replace the current
            local portfolio positions.
          </p>
          <DataTableWrapper>
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b border-muted/30 text-xs uppercase tracking-widest text-muted">
                  <th className="px-4 py-2 text-left">Symbol</th>
                  <th className="px-4 py-2 text-right">Lot</th>
                  <th className="px-4 py-2 text-right">Average Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-muted/20">
                {result.positions.map((position) => (
                  <tr key={position.symbol}>
                    <td className="px-4 py-2 font-mono">{position.symbol}</td>
                    <td className="px-4 py-2 text-right tabular-nums">{position.lots}</td>
                    <td className="px-4 py-2 text-right tabular-nums">
                      {new Intl.NumberFormat("id-ID").format(Math.round(position.avg_price))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </DataTableWrapper>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => handleConfirm(result.positions)}
              className="rounded border border-emerald-500/40 px-4 py-2 text-sm text-emerald-300 hover:bg-emerald-500/10"
              type="button"
            >
              Confirm import
            </button>
            <button
              onClick={() => {
                setPhase("upload");
                setResult(null);
              }}
              className="text-sm text-muted underline hover:text-fg"
              type="button"
            >
              Cancel
            </button>
          </div>
        </section>
      ) : null}

      {phase === "saving" ? <p className="text-sm text-muted">Saving portfolio positions...</p> : null}

      {phase === "error" ? (
        <RuntimeErrorState
          title="Portfolio import could not be completed"
          message={errorMsg}
          recommendedCommand="uv run python -m scripts.runtime status --json"
          actionLabel="Check runtime status"
        />
      ) : null}
    </main>
  );
}

function PageHeader(): React.ReactElement {
  return (
    <header>
      <div className="flex items-center gap-3">
        <p className="text-sm uppercase tracking-widest text-muted">SahamLens / Portfolio</p>
        <Link href="/portfolio" className="text-xs text-accent hover:underline">
          Back to Portfolio
        </Link>
      </div>
      <h1 className="mt-1 text-3xl font-semibold">Import CSV</h1>
      <p className="mt-2 text-sm text-muted">
        Minimum format: <code className="font-mono text-xs">symbol, lots, avg_price</code>.
        Some common aliases are detected automatically.
      </p>
    </header>
  );
}
