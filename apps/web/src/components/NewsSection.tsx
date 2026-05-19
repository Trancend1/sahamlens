/**
 * News + AI summary panel for the stock detail page.
 *
 * Server component. Renders a grid of NewsCard, or a muted empty state when
 * no summarized news for the open ticker exists yet.
 */

import { NewsCard } from "@/components/NewsCard";
import type { NewsRecent } from "@/lib/stockDetail";

interface NewsSectionProps {
  items: NewsRecent[];
  symbol: string;
}

export function NewsSection({ items, symbol }: NewsSectionProps): React.ReactElement {
  if (items.length === 0) {
    return (
      <section
        className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm text-muted"
        data-empty
      >
        <p className="font-medium text-fg/80">Belum ada news ter-summarize untuk {symbol}.</p>
        <pre className="mt-2 whitespace-pre-wrap text-xs">
          uv run python -m scripts.ingest_news{"\n"}
          uv run python -m scripts.summarize_news --from-watchlist --limit 10
        </pre>
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-3">
      <header className="flex items-baseline justify-between">
        <h2 className="text-sm uppercase tracking-widest text-muted">News + AI ringkasan</h2>
        <span className="text-[10px] text-muted">
          {items.length} item · model: {hostFromConfidence(items)}
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
  const lo = items.filter((i) => i.confidence < 0.6).length;
  return lo > 0 ? `${lo} low-confidence` : "all ≥0.6 conf";
}
