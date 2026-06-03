import { NewsCard } from "@/components/NewsCard";
import { EmptyState } from "@/components/ui/EmptyState";
import type { NewsRecent } from "@/lib/stockDetail";

interface NewsSectionProps {
  items: NewsRecent[];
  symbol: string;
}

export function NewsSection({ items, symbol }: NewsSectionProps): React.ReactElement {
  if (items.length === 0) {
    return (
      <div data-empty>
        <EmptyState
          title={`No summarized news yet for ${symbol}`}
          description="Ingest and summarize validated RSS metadata before using news context for this ticker."
          actionLabel="Refresh news metadata"
          command="uv run python -m scripts.ingest_news"
        />
      </div>
    );
  }

  return (
    <section className="flex flex-col gap-3">
      <header className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="text-sm uppercase tracking-widest text-muted">News + AI Summary</h2>
        <span className="text-[10px] text-muted">
          {items.length} item / confidence: {hostFromConfidence(items)}
        </span>
      </header>
      <div className="grid gap-3 md:grid-cols-2">
        {items.map((item) => (
          <NewsCard key={item.news_id} news={item} />
        ))}
      </div>
    </section>
  );
}

function hostFromConfidence(items: NewsRecent[]): string {
  const lowConfidenceCount = items.filter((item) => item.confidence < 0.6).length;
  return lowConfidenceCount > 0 ? `${lowConfidenceCount} low-confidence` : "all at least 0.6";
}
