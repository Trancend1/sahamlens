/**
 * Locale-aware relative time formatting + freshness tier classification.
 *
 * `formatRelativeTime` uses Intl.RelativeTimeFormat with id-ID locale.
 * `freshnessTier` partitions ISO timestamps into UI color tiers.
 */

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

export type FreshnessTier = "fresh" | "stale" | "old";

const RTF = new Intl.RelativeTimeFormat("id", { numeric: "auto" });

export function formatRelativeTime(iso: string, now: Date = new Date()): string {
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return iso;
  const diffMs = then.getTime() - now.getTime();
  const abs = Math.abs(diffMs);

  if (abs < HOUR) {
    const minutes = Math.round(diffMs / (60 * 1000));
    return RTF.format(minutes, "minute");
  }
  if (abs < DAY) {
    return RTF.format(Math.round(diffMs / HOUR), "hour");
  }
  if (abs < 7 * DAY) {
    return RTF.format(Math.round(diffMs / DAY), "day");
  }
  if (abs < 30 * DAY) {
    return RTF.format(Math.round(diffMs / (7 * DAY)), "week");
  }
  return RTF.format(Math.round(diffMs / (30 * DAY)), "month");
}

export function freshnessTier(iso: string, now: Date = new Date()): FreshnessTier {
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return "old";
  const ageMs = now.getTime() - then.getTime();
  if (ageMs < 24 * HOUR) return "fresh";
  if (ageMs <= 72 * HOUR) return "stale";
  return "old";
}
