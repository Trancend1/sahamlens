import type { JournalCritique, CritiqueCheck, RiskFlag, CritiqueStatus } from "@/lib/journal";

const FLAG_STYLES: Record<RiskFlag, { bg: string; text: string; label: string }> = {
  green: { bg: "bg-green-500/10 border-green-500/30", text: "text-green-400", label: "Risiko Rendah" },
  amber: { bg: "bg-yellow-500/10 border-yellow-500/30", text: "text-yellow-400", label: "Perlu Perhatian" },
  red: { bg: "bg-red-500/10 border-red-500/30", text: "text-red-400", label: "Risiko Tinggi" },
  incomplete: { bg: "bg-muted/10 border-muted/30", text: "text-muted", label: "Data Tidak Lengkap" },
};

const STATUS_BADGE: Record<CritiqueStatus, { cls: string; label: string }> = {
  ok: { cls: "bg-green-500/15 text-green-400 border-green-500/30", label: "ok" },
  weak: { cls: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30", label: "lemah" },
  missing: { cls: "bg-red-500/15 text-red-400 border-red-500/30", label: "kosong" },
};

const CATEGORY_LABELS: Record<string, string> = {
  thesis: "Thesis",
  invalidation: "Invalidasi",
  risk: "Risiko",
  catalyst: "Katalis",
  emotion: "Emosi",
  liquidity: "Likuiditas",
};

function CheckRow({ check }: { check: CritiqueCheck }) {
  const badge = STATUS_BADGE[check.status];
  return (
    <li className="border-b border-muted/15 py-3 last:border-0">
      <div className="flex items-center gap-2">
        <span className="w-24 text-xs font-medium text-fg">
          {CATEGORY_LABELS[check.category] ?? check.category}
        </span>
        <span className={`rounded border px-1.5 py-0.5 text-xs font-mono ${badge.cls}`}>
          {badge.label}
        </span>
      </div>
      <p className="mt-1 text-sm text-fg/90">{check.finding}</p>
      <p className="mt-1 text-xs text-accent italic">{check.suggested_question}</p>
    </li>
  );
}

export default function CritiquePanel({ critique }: { critique: JournalCritique }) {
  const flag = FLAG_STYLES[critique.overall_risk_flag];
  return (
    <section className="mt-6 rounded-md border border-muted/30 bg-white/[0.02]">
      <div className={`flex items-center gap-3 rounded-t-md border-b border-muted/20 px-5 py-3 ${flag.bg}`}>
        <span className={`text-sm font-semibold ${flag.text}`}>{flag.label}</span>
        <span className="text-xs text-muted">Kritik AI — Bukan Saran Keuangan</span>
      </div>

      <ul className="px-5 py-2">
        {critique.checks.map((c) => (
          <CheckRow key={c.category} check={c} />
        ))}
      </ul>

      {critique.caveats.length > 0 && (
        <div className="border-t border-muted/15 px-5 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">Catatan</p>
          <ul className="mt-1 list-disc pl-4">
            {critique.caveats.map((c, i) => (
              <li key={i} className="text-xs text-fg/80">
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-b-md border-t border-muted/15 bg-white/[0.01] px-5 py-2">
        <p className="text-xs text-muted">
          AI hanya mengajukan pertanyaan — tidak menyetujui atau menolak trade. Keputusan sepenuhnya
          ada di tangan Anda.
        </p>
      </div>
    </section>
  );
}
