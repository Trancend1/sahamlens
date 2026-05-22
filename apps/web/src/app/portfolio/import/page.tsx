"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import type { ImportResult, PortfolioPosition } from "@/lib/portfolio";

type ImportPhase = "upload" | "preview" | "mapping" | "saving" | "done" | "error";

export default function PortfolioImportPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<ImportPhase>("upload");
  const [csvContent, setCsvContent] = useState("");
  const [result, setResult] = useState<ImportResult | null>(null);
  const [fieldMap, setFieldMap] = useState<Record<string, string>>({});
  const [errorMsg, setErrorMsg] = useState("");

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setCsvContent(text);
    await parseCSV(text, undefined);
  }

  async function parseCSV(csv: string, fm: Record<string, string> | undefined) {
    setErrorMsg("");
    try {
      const res = await fetch("/api/portfolio/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv_content: csv, field_map: fm }),
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
    } catch (err) {
      setErrorMsg(String(err));
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
        const body: { error?: string } = await res.json();
        setErrorMsg(body.error ?? "Gagal menyimpan");
        setPhase("error");
        return;
      }
      setPhase("done");
    } catch (err) {
      setErrorMsg(String(err));
      setPhase("error");
    }
  }

  async function handleFieldMapSubmit() {
    await parseCSV(csvContent, fieldMap);
  }

  if (phase === "done") {
    return (
      <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
        <header>
          <div className="flex items-center gap-3">
            <p className="text-sm uppercase tracking-widest text-muted">SahamLens · Portfolio</p>
            <Link href="/portfolio" className="text-xs text-accent hover:underline">
              ← Portfolio
            </Link>
          </div>
        </header>
        <div className="rounded-md border border-green-500/30 bg-green-500/5 px-5 py-4">
          <p className="text-sm font-medium text-green-400">Import berhasil</p>
        </div>
        <Link
          href="/portfolio"
          className="w-fit rounded border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10"
        >
          Lihat Portfolio →
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <header>
        <div className="flex items-center gap-3">
          <p className="text-sm uppercase tracking-widest text-muted">SahamLens · Portfolio</p>
          <Link href="/portfolio" className="text-xs text-accent hover:underline">
            ← Portfolio
          </Link>
        </div>
        <h1 className="mt-1 text-3xl font-semibold">Import CSV</h1>
        <p className="mt-2 text-sm text-muted">
          Format minimal: kolom <code className="font-mono text-xs">symbol, lots, avg_price</code>.
          Alias lain dikenali otomatis (kode, lot, harga, dll).
        </p>
      </header>

      {phase === "upload" && (
        <section className="rounded-md border border-muted/30 bg-white/[0.02] p-6">
          <label className="flex cursor-pointer flex-col items-center gap-3 text-sm text-muted hover:text-fg">
            <span className="text-3xl">↑</span>
            <span>Pilih file CSV</span>
            <input type="file" accept=".csv,text/csv" onChange={handleFile} className="hidden" />
          </label>
        </section>
      )}

      {result?.warnings && result.warnings.length > 0 && (
        <section className="rounded-md border border-amber-500/40 bg-amber-500/[0.06] p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-amber-300">
            Peringatan
          </p>
          <ul className="mt-2 space-y-1 text-sm text-amber-200/80">
            {result.warnings.map((w, i) => (
              <li key={i}>• {w}</li>
            ))}
          </ul>
        </section>
      )}

      {phase === "mapping" && result && (
        <section className="space-y-4 rounded-md border border-muted/30 bg-white/[0.02] p-5">
          <p className="text-sm font-medium">
            Kolom tidak terdeteksi otomatis. Pilih kolom yang sesuai:
          </p>
          {(["symbol", "lots", "price"] as const).map((canonical) => (
            <div key={canonical}>
              <label className="mb-1 block text-xs uppercase tracking-widest text-muted">
                {canonical === "price" ? "Harga Beli (avg)" : canonical}
              </label>
              <select
                value={fieldMap[canonical] ?? ""}
                onChange={(e) => setFieldMap((prev) => ({ ...prev, [canonical]: e.target.value }))}
                className="w-full rounded border border-muted/30 bg-transparent px-3 py-2 text-sm"
              >
                <option value="">-- pilih kolom --</option>
                {result.detected_columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
            </div>
          ))}
          <button
            onClick={handleFieldMapSubmit}
            disabled={!fieldMap.symbol || !fieldMap.lots || !fieldMap.price}
            className="rounded border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10 disabled:opacity-40"
          >
            Proses →
          </button>
        </section>
      )}

      {phase === "preview" && result && result.positions.length > 0 && (
        <section className="space-y-4">
          <p className="text-sm text-muted">
            {result.positions.length} posisi terdeteksi. Konfirmasi untuk menyimpan (replace semua data
            sebelumnya).
          </p>
          <div className="overflow-x-auto rounded-md border border-muted/30">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-muted/30 text-xs uppercase tracking-widest text-muted">
                  <th className="px-4 py-2 text-left">Symbol</th>
                  <th className="px-4 py-2 text-right">Lot</th>
                  <th className="px-4 py-2 text-right">Avg Beli</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-muted/20">
                {result.positions.map((p) => (
                  <tr key={p.symbol}>
                    <td className="px-4 py-2 font-mono">{p.symbol}</td>
                    <td className="px-4 py-2 text-right tabular-nums">{p.lots}</td>
                    <td className="px-4 py-2 text-right tabular-nums">
                      {new Intl.NumberFormat("id-ID").format(Math.round(p.avg_price))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => handleConfirm(result.positions)}
              className="rounded border border-emerald-500/40 px-4 py-2 text-sm text-emerald-300 hover:bg-emerald-500/10"
            >
              Konfirmasi Import
            </button>
            <button
              onClick={() => {
                setPhase("upload");
                setResult(null);
              }}
              className="text-sm text-muted underline hover:text-fg"
            >
              Batalkan
            </button>
          </div>
        </section>
      )}

      {phase === "saving" && <p className="text-sm text-muted">Menyimpan...</p>}

      {phase === "error" && (
        <section className="rounded-md border border-red-500/40 bg-red-500/[0.05] p-4">
          <p className="text-sm font-medium text-red-300">Error</p>
          <pre className="mt-2 whitespace-pre-wrap text-xs text-red-200">{errorMsg}</pre>
          <button
            onClick={() => setPhase("upload")}
            className="mt-3 text-xs text-muted underline"
          >
            Coba lagi
          </button>
        </section>
      )}
    </main>
  );
}
