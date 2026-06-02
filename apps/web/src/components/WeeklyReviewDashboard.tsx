import Link from "next/link";
import type { WeeklyFindingSeverity, WeeklyReviewRun } from "@/lib/journalReview";

const SEVERITY_COPY: Record<WeeklyFindingSeverity, { label: string; className: string }> = {
  info: { label: "Info", className: "border-sky-500/40 text-sky-300" },
  warning: { label: "Warning", className: "border-amber-500/40 text-amber-300" },
  critical: { label: "Critical", className: "border-red-500/40 text-red-300" },
};

interface Props {
  reviews: WeeklyReviewRun[];
  error: string | null;
}

export function WeeklyReviewDashboard({ reviews, error }: Props): React.ReactElement {
  const latest = reviews[0] ?? null;
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">
          <Link href="/" className="hover:text-fg">
            SahamLens
          </Link>{" "}
          / V1-S4
        </p>
        <h1 className="mt-1 text-3xl font-semibold">Weekly Journal Review</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Behavior review from local journal entries and simple named strategy-rule checks.
        </p>
      </header>

      {error ? <ErrorPanel error={error} /> : null}
      {!error && latest ? <ReviewContent review={latest} /> : null}
      {!error && !latest ? <EmptyState /> : null}
    </main>
  );
}

function ReviewContent({ review }: { review: WeeklyReviewRun }): React.ReactElement {
  return (
    <>
      <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
        <p className="text-xs uppercase tracking-widest text-muted">
          {formatDate(review.period_start)} to {formatDate(review.period_end)}
        </p>
        <h2 className="mt-2 text-xl font-semibold">{review.summary}</h2>
        <p className="mt-2 text-sm text-muted">Generated {formatDate(review.generated_at)}</p>
      </section>
      <Summary review={review} />
      <Findings review={review} />
      <EvidenceAndCaveats review={review} />
    </>
  );
}

function Summary({ review }: { review: WeeklyReviewRun }): React.ReactElement {
  const items = [
    ["Journal Entries", review.journal_entry_count],
    ["Rule Evaluations", review.rule_evaluation_count],
    ["Violations", review.violation_count],
    ["Needs Data", review.needs_data_count],
  ] as const;
  return (
    <section className="grid gap-3 sm:grid-cols-4">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-md border border-muted/30 bg-white/[0.02] p-4">
          <p className="text-xs uppercase tracking-widest text-muted">{label}</p>
          <p className="mt-2 text-2xl font-semibold">{value}</p>
        </div>
      ))}
    </section>
  );
}

function Findings({ review }: { review: WeeklyReviewRun }): React.ReactElement {
  return (
    <section className="grid gap-3">
      <h2 className="text-sm font-medium">Findings</h2>
      {review.findings.map((finding) => {
        const severity = SEVERITY_COPY[finding.severity];
        return (
          <article key={finding.finding_id} className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-widest text-muted">{finding.finding_type}</p>
                <h3 className="mt-1 text-lg font-semibold">{finding.title}</h3>
              </div>
              <span className={`rounded border px-2 py-1 text-xs uppercase tracking-widest ${severity.className}`}>
                {severity.label}
              </span>
            </div>
            <p className="mt-3 text-sm text-fg">{finding.detail}</p>
            <List title="Evidence" items={finding.evidence} />
            <List title="Caveats" items={finding.caveats} />
          </article>
        );
      })}
    </section>
  );
}

function EvidenceAndCaveats({ review }: { review: WeeklyReviewRun }): React.ReactElement {
  return (
    <section className="grid gap-3 md:grid-cols-2">
      <div className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
        <List title="Evidence" items={review.evidence} />
      </div>
      <div className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
        <List title="Caveats" items={review.caveats} />
      </div>
    </section>
  );
}

function EmptyState(): React.ReactElement {
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm">
      <p className="font-medium">Belum ada weekly review.</p>
      <p className="mt-2 text-muted">
        Run{" "}
        <code className="font-mono">
          uv run python -m scripts.journal_review --json review generate --start 2026-05-25 --end
          2026-06-01
        </code>{" "}
        after journal entries are ready.
      </p>
    </section>
  );
}

function ErrorPanel({ error }: { error: string }): React.ReactElement {
  return (
    <section className="rounded-md border border-red-500/40 bg-red-500/[0.05] p-5 text-sm">
      <p className="font-medium text-red-300">Gagal membaca weekly review.</p>
      <p className="mt-2 text-muted">
        Pastikan migration terbaru sudah jalan:{" "}
        <code className="font-mono">uv run python -m scripts.migrate</code>
      </p>
      <pre className="mt-3 whitespace-pre-wrap text-xs text-red-200">{error}</pre>
    </section>
  );
}

function List({ title, items }: { title: string; items: string[] }): React.ReactElement | null {
  if (items.length === 0) return null;
  return (
    <div className="mt-3">
      <p className="text-xs uppercase tracking-widest text-muted">{title}</p>
      <ul className="mt-2 list-inside list-disc text-sm text-muted">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toISOString().slice(0, 10);
  } catch {
    return iso;
  }
}
