"use client";

import Link from "next/link";
import { useState, useMemo } from "react";
import { CoolingOffBanner } from "./CoolingOffBanner";
import CritiquePanel from "./CritiquePanel";
import { calcPositionSize } from "@/lib/journal-client";
import type { TradePlan, JournalCritique, SetupType, EmotionLevel } from "@/lib/journal-client";

const SETUP_TYPES: { value: SetupType; label: string }[] = [
  { value: "breakout", label: "Breakout" },
  { value: "ma_cross", label: "MA Cross" },
  { value: "mean_reversion", label: "Mean Reversion" },
  { value: "support_bounce", label: "Support Bounce" },
  { value: "other", label: "Lainnya" },
];

const EMOTION_LEVELS: { value: EmotionLevel; label: string }[] = [
  { value: "calm", label: "Tenang" },
  { value: "excited", label: "Bersemangat" },
  { value: "fearful", label: "Takut" },
  { value: "greedy", label: "Rakus" },
  { value: "uncertain", label: "Ragu" },
];

function formatRp(n: number): string {
  if (n === 0) return "Rp 0";
  return "Rp " + n.toLocaleString("id-ID");
}

function FieldLabel({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) {
  return (
    <label htmlFor={htmlFor} className="block text-xs font-medium uppercase tracking-wide text-muted">
      {children}
    </label>
  );
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`mt-1 block w-full rounded border border-muted/30 bg-white/[0.03] px-3 py-2 text-sm text-fg placeholder:text-muted/50 focus:border-accent/60 focus:outline-none ${props.className ?? ""}`}
    />
  );
}

function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      rows={3}
      {...props}
      className={`mt-1 block w-full rounded border border-muted/30 bg-white/[0.03] px-3 py-2 text-sm text-fg placeholder:text-muted/50 focus:border-accent/60 focus:outline-none ${props.className ?? ""}`}
    />
  );
}

function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={`mt-1 block w-full rounded border border-muted/30 bg-bg px-3 py-2 text-sm text-fg focus:border-accent/60 focus:outline-none ${props.className ?? ""}`}
    />
  );
}

type FormState = {
  symbol: string;
  setup_type: SetupType;
  thesis: string;
  entry_plan: string;
  entry_price: string;
  stop_level: string;
  invalidation: string;
  target: string;
  portfolio_value: string;
  risk_percent: string;
  emotion: EmotionLevel | "";
};

const INITIAL: FormState = {
  symbol: "",
  setup_type: "breakout",
  thesis: "",
  entry_plan: "",
  entry_price: "",
  stop_level: "",
  invalidation: "",
  target: "",
  portfolio_value: "",
  risk_percent: "1",
  emotion: "",
};

export default function TradePlanForm() {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [submitState, setSubmitState] = useState<"idle" | "submitting" | "saved">("idle");
  const [savedPlan, setSavedPlan] = useState<TradePlan | null>(null);
  const [critiqueState, setCritiqueState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [critique, setCritique] = useState<JournalCritique | null>(null);
  const [critiqueError, setCritiqueError] = useState<string>("");
  const [submitError, setSubmitError] = useState<string>("");

  const calc = useMemo(() => {
    const pv = parseFloat(form.portfolio_value.replace(/[,.]/g, "")) || 0;
    const rp = (parseFloat(form.risk_percent) || 0) / 100;
    const ep = parseFloat(form.entry_price) || 0;
    const sl = parseFloat(form.stop_level) || 0;
    return calcPositionSize(pv, rp, ep, sl);
  }, [form.portfolio_value, form.risk_percent, form.entry_price, form.stop_level]);

  function set(field: keyof FormState) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError("");
    setSubmitState("submitting");

    const payload = {
      symbol: form.symbol,
      setup_type: form.setup_type,
      thesis: form.thesis,
      entry_plan: form.entry_plan,
      stop_level: parseFloat(form.stop_level) || 0,
      invalidation: form.invalidation,
      target: form.target,
      position_size_rupiah: calc.positionSizeRupiah,
      max_loss_rupiah: calc.maxLossRupiah,
      emotion: form.emotion || null,
    };

    try {
      const res = await fetch("/api/journal/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = (await res.json()) as { error?: string; detail?: string };
        setSubmitError(body.detail ?? body.error ?? "Gagal menyimpan plan");
        setSubmitState("idle");
        return;
      }
      const plan = (await res.json()) as TradePlan;
      setSavedPlan(plan);
      setSubmitState("saved");
    } catch (err) {
      setSubmitError(String(err));
      setSubmitState("idle");
    }
  }

  async function handleCritique() {
    if (!savedPlan) return;
    setCritiqueState("loading");
    setCritiqueError("");
    try {
      const res = await fetch(`/api/journal/critique/${savedPlan.id}`, { method: "POST" });
      if (!res.ok) {
        const body = (await res.json()) as { error?: string };
        setCritiqueError(body.error ?? "Gagal mendapatkan kritik");
        setCritiqueState("error");
        return;
      }
      const data = (await res.json()) as JournalCritique;
      setCritique(data);
      setCritiqueState("done");
    } catch (err) {
      setCritiqueError(String(err));
      setCritiqueState("error");
    }
  }

  if (submitState === "saved" && savedPlan) {
    return (
      <div className="space-y-4">
        <div className="rounded-md border border-green-500/30 bg-green-500/5 px-5 py-4">
          <p className="text-sm font-medium text-green-400">Plan tersimpan</p>
          <p className="mt-1 text-xs text-muted">
            ID: <span className="font-mono">{savedPlan.id}</span> · {savedPlan.symbol} ·{" "}
            {savedPlan.setup_type}
          </p>
        </div>

        {critiqueState === "idle" && (
          <button
            onClick={handleCritique}
            className="rounded border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10"
          >
            Minta Kritik AI
          </button>
        )}
        {critiqueState === "loading" && (
          <p className="text-sm text-muted">Memproses kritik... (30–60 detik)</p>
        )}
        {critiqueState === "error" && (
          <p className="text-sm text-red-400">{critiqueError}</p>
        )}
        {critiqueState === "done" && critique && (
          <>
            <CritiquePanel critique={critique} />
            <CoolingOffBanner
              emotion={form.emotion || null}
              riskFlag={critique.overall_risk_flag}
            />
          </>
        )}

        <div className="mt-2 flex items-center gap-4">
          <Link href="/journal" className="text-xs text-accent hover:underline">
            Lihat di Journal →
          </Link>
          <button
            onClick={() => {
              setForm(INITIAL);
              setSubmitState("idle");
              setSavedPlan(null);
              setCritiqueState("idle");
              setCritique(null);
            }}
            className="text-xs text-muted underline hover:text-fg"
          >
            Buat plan baru
          </button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Symbol + Setup */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <FieldLabel htmlFor="symbol">Saham *</FieldLabel>
          <Input
            id="symbol"
            required
            placeholder="BBCA"
            value={form.symbol}
            onChange={set("symbol")}
          />
        </div>
        <div>
          <FieldLabel htmlFor="setup_type">Setup *</FieldLabel>
          <Select id="setup_type" value={form.setup_type} onChange={set("setup_type")}>
            {SETUP_TYPES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {/* Thesis */}
      <div>
        <FieldLabel htmlFor="thesis">Thesis *</FieldLabel>
        <Textarea
          id="thesis"
          required
          placeholder="Mengapa trade ini menarik? Apa yang membuat setup ini valid?"
          value={form.thesis}
          onChange={set("thesis")}
        />
      </div>

      {/* Entry plan */}
      <div>
        <FieldLabel htmlFor="entry_plan">Entry Plan *</FieldLabel>
        <Textarea
          id="entry_plan"
          required
          placeholder="Kondisi entry: harga, pattern, konfirmasi apa yang diperlukan?"
          value={form.entry_plan}
          onChange={set("entry_plan")}
        />
      </div>

      {/* Price inputs for calc */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <FieldLabel htmlFor="entry_price">Harga Entry (Rp/saham)</FieldLabel>
          <Input
            id="entry_price"
            type="number"
            min="0"
            step="any"
            placeholder="9500"
            value={form.entry_price}
            onChange={set("entry_price")}
          />
        </div>
        <div>
          <FieldLabel htmlFor="stop_level">Stop Loss (Rp/saham) *</FieldLabel>
          <Input
            id="stop_level"
            type="number"
            required
            min="0"
            step="any"
            placeholder="9200"
            value={form.stop_level}
            onChange={set("stop_level")}
          />
        </div>
      </div>

      {/* Risk params */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <FieldLabel htmlFor="portfolio_value">Nilai Portfolio (Rp)</FieldLabel>
          <Input
            id="portfolio_value"
            type="number"
            min="0"
            placeholder="100000000"
            value={form.portfolio_value}
            onChange={set("portfolio_value")}
          />
        </div>
        <div>
          <FieldLabel htmlFor="risk_percent">Risk per Trade (%)</FieldLabel>
          <Input
            id="risk_percent"
            type="number"
            min="0"
            max="10"
            step="0.1"
            placeholder="1"
            value={form.risk_percent}
            onChange={set("risk_percent")}
          />
        </div>
      </div>

      {/* Live calc output */}
      {calc.lots > 0 && (
        <div className="rounded border border-accent/20 bg-accent/5 px-4 py-3 text-sm">
          <p className="font-medium text-accent">Kalkulator Posisi</p>
          <div className="mt-2 grid grid-cols-3 gap-3 text-xs">
            <div>
              <span className="text-muted">Lots</span>
              <p className="font-mono text-fg">{calc.lots.toLocaleString("id-ID")}</p>
            </div>
            <div>
              <span className="text-muted">Ukuran posisi</span>
              <p className="font-mono text-fg">{formatRp(calc.positionSizeRupiah)}</p>
            </div>
            <div>
              <span className="text-muted">Max loss</span>
              <p className="font-mono text-fg">{formatRp(calc.maxLossRupiah)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Invalidation */}
      <div>
        <FieldLabel htmlFor="invalidation">Invalidasi Thesis *</FieldLabel>
        <Textarea
          id="invalidation"
          required
          placeholder="Kondisi apa yang membuktikan thesis ini salah?"
          value={form.invalidation}
          onChange={set("invalidation")}
        />
      </div>

      {/* Target */}
      <div>
        <FieldLabel htmlFor="target">Target Exit *</FieldLabel>
        <Input
          id="target"
          required
          placeholder="10200 atau resistance berikutnya"
          value={form.target}
          onChange={set("target")}
        />
      </div>

      {/* Emotion */}
      <div className="w-1/2">
        <FieldLabel htmlFor="emotion">Kondisi Emosi</FieldLabel>
        <Select id="emotion" value={form.emotion} onChange={set("emotion")}>
          <option value="">— pilih —</option>
          {EMOTION_LEVELS.map((e) => (
            <option key={e.value} value={e.value}>
              {e.label}
            </option>
          ))}
        </Select>
      </div>

      {submitError && (
        <p className="text-sm text-red-400">{submitError}</p>
      )}

      <button
        type="submit"
        disabled={submitState === "submitting"}
        className="rounded bg-accent/20 px-5 py-2 text-sm font-medium text-accent hover:bg-accent/30 disabled:opacity-50"
      >
        {submitState === "submitting" ? "Menyimpan..." : "Simpan Trade Plan"}
      </button>

      <p className="text-xs text-muted">
        Bukan saran keuangan. AI menjelaskan, Anda yang memutuskan.
      </p>
    </form>
  );
}
