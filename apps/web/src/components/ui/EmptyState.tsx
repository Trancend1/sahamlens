import Link from "next/link";

type EmptyTone = "neutral" | "healthy" | "warning";

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  command?: string;
  tone?: EmptyTone;
}

const TONE_CLASS: Record<EmptyTone, string> = {
  neutral: "border-muted/30 bg-white/[0.02]",
  healthy: "border-emerald-500/30 bg-emerald-500/[0.04]",
  warning: "border-amber-500/30 bg-amber-500/[0.04]",
};

export function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
  tone = "neutral",
}: EmptyStateProps): React.ReactElement {
  return (
    <section className={`rounded-md border p-5 text-sm ${TONE_CLASS[tone]}`}>
      <p className="font-medium text-fg">{title}</p>
      <p className="mt-2 max-w-2xl text-muted">{description}</p>
      {actionLabel ? (
        actionHref ? (
          <Link
            href={actionHref}
            className="mt-4 inline-flex rounded border border-accent/40 px-3 py-1.5 text-sm text-accent hover:bg-accent/10"
          >
            {actionLabel}
          </Link>
        ) : (
          <p className="mt-4 text-sm font-medium text-accent">{actionLabel}</p>
        )
      ) : null}
    </section>
  );
}
