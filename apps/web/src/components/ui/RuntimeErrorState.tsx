import Link from "next/link";
import { CommandBlock } from "./CommandBlock";

interface RuntimeErrorStateProps {
  title: string;
  message: string;
  details?: string | null;
  recommendedCommand?: string | null;
  actionLabel?: string;
  actionHref?: string;
}

export function RuntimeErrorState({
  title,
  message,
  details,
  recommendedCommand,
  actionLabel = "Check runtime status",
  actionHref = "/data-quality",
}: RuntimeErrorStateProps): React.ReactElement {
  const safeDetails = sanitizeUserFacingDetail(details);
  return (
    <section className="rounded-md border border-red-500/40 bg-red-500/[0.05] p-5 text-sm">
      <p className="font-medium text-red-300">{title}</p>
      <p className="mt-2 max-w-2xl text-fg">{sanitizeUserFacingDetail(message)}</p>
      {safeDetails ? <p className="mt-2 max-w-2xl text-muted">{safeDetails}</p> : null}
      <div className="mt-4 flex flex-wrap gap-3">
        <Link
          href={actionHref}
          className="rounded border border-accent/40 px-3 py-1.5 text-sm text-accent hover:bg-accent/10"
        >
          {actionLabel}
        </Link>
      </div>
      {recommendedCommand ? <CommandBlock command={recommendedCommand} /> : null}
    </section>
  );
}

export function sanitizeUserFacingDetail(value?: string | null): string {
  if (!value) return "";
  if (containsRawRuntimeDetail(value)) {
    return "The local command could not complete. Check runtime readiness or run the recommended recovery command below.";
  }
  return value.length > 280 ? `${value.slice(0, 277)}...` : value;
}

function containsRawRuntimeDetail(value: string): boolean {
  return [
    "Traceback",
    "sqlite3.",
    "OperationalError",
    "CatalogException",
    "no such table",
    "D:/",
    "D:\\",
    "C:/",
    "C:\\",
  ].some((needle) => value.includes(needle));
}
