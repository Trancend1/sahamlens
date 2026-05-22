import { FreshnessBadge } from "./FreshnessBadge";

interface StockFreshnessBarProps {
  lastDate: string | null | undefined;
}

export function StockFreshnessBar({ lastDate }: StockFreshnessBarProps) {
  if (!lastDate) return null;
  return (
    <div className="flex items-center gap-2 text-xs text-muted">
      <span>Data per {lastDate}</span>
      <FreshnessBadge iso={lastDate} />
    </div>
  );
}
