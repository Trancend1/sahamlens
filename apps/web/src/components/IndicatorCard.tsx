/**
 * 5-block indicator card per PRD §9.2.
 * Blocks: (1) what it measures (2) current value (3) interpretation
 *         (4) common false signal (5) time-horizon note.
 *
 * Presentational only; no fetching. Caller passes value + optional current price.
 */

import {
  INDICATOR_META,
  type IndicatorKey,
  type InterpretContext,
} from "@/lib/indicatorMeta";

const CATEGORY_BADGE: Record<string, string> = {
  trend: "border-accent/40 text-accent",
  momentum: "border-amber-500/40 text-amber-300",
  volume: "border-muted/40 text-muted",
};

interface IndicatorCardProps {
  indicator: IndicatorKey;
  value: number | null;
  currentPrice?: number | null;
}

export function IndicatorCard({
  indicator,
  value,
  currentPrice = null,
}: IndicatorCardProps): React.ReactElement {
  const meta = INDICATOR_META[indicator];
  const ctx: InterpretContext = { price: currentPrice };

  return (
    <article
      className="rounded-md border border-muted/30 bg-white/[0.02] p-4 text-sm leading-relaxed"
      data-indicator={indicator}
    >
      <header className="mb-3 flex items-baseline justify-between gap-3">
        <h3 className="font-semibold tracking-tight">{meta.label}</h3>
        <span
          className={`rounded border px-2 py-0.5 text-[10px] uppercase tracking-widest ${
            CATEGORY_BADGE[meta.category] ?? "border-muted/40 text-muted"
          }`}
        >
          {meta.category}
        </span>
      </header>

      <p className="font-mono text-2xl font-semibold tabular-nums">
        {value == null ? <span className="text-muted">—</span> : meta.formatValue(value)}
      </p>

      <dl className="mt-4 space-y-3 text-xs">
        <Block label="Apa yang diukur" body={meta.whatItMeasures} />
        <Block
          label="Interpretasi"
          body={value == null ? "Belum ada nilai (warm-up window)." : meta.interpret(value, ctx)}
        />
        <Block label="False signal umum" body={meta.falseSignal} />
        <Block label="Time horizon" body={meta.horizonNote} />
      </dl>
    </article>
  );
}

interface BlockProps {
  label: string;
  body: string;
}

function Block({ label, body }: BlockProps): React.ReactElement {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-widest text-muted">{label}</dt>
      <dd className="mt-0.5 text-fg/90">{body}</dd>
    </div>
  );
}
