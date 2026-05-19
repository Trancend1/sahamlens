/**
 * Pill badge that surfaces a timestamp's age tier + locale-aware relative label.
 */

import { formatRelativeTime, freshnessTier } from "@/lib/dateTime";

const TIER_CLASS: Record<string, string> = {
  fresh: "border-emerald-500/40 text-emerald-300",
  stale: "border-amber-500/40 text-amber-300",
  old: "border-muted/40 text-muted",
};

interface FreshnessBadgeProps {
  iso: string;
}

export function FreshnessBadge({ iso }: FreshnessBadgeProps): React.ReactElement {
  const tier = freshnessTier(iso);
  const label = formatRelativeTime(iso);
  return (
    <span
      className={`rounded border px-2 py-0.5 text-[10px] uppercase tracking-widest ${
        TIER_CLASS[tier] ?? TIER_CLASS.old
      }`}
      data-tier={tier}
      title={iso}
    >
      {label}
    </span>
  );
}
