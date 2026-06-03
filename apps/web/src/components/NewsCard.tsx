import { FreshnessBadge } from "@/components/FreshnessBadge";
import type { NewsRecent, SentimentLabel, SourceQuality } from "@/lib/stockDetail";

const SENTIMENT_CLASS: Record<SentimentLabel, string> = {
  bullish: "border-emerald-500/40 text-emerald-300",
  bearish: "border-red-500/40 text-red-300",
  mixed: "border-amber-500/40 text-amber-300",
  neutral: "border-muted/40 text-muted",
};

const SENTIMENT_LABEL: Record<SentimentLabel, string> = {
  bullish: "Bullish",
  bearish: "Bearish",
  mixed: "Mixed",
  neutral: "Neutral",
};

const QUALITY_LABEL: Record<SourceQuality, string> = {
  official: "Official source",
  reputable_media: "Reputable media",
  blog: "Blog / opinion",
  unknown: "Unknown source",
};

interface NewsCardProps {
  news: NewsRecent;
}

export function NewsCard({ news }: NewsCardProps): React.ReactElement {
  const lowConfidence = news.confidence < 0.6;
  const sentimentClass = SENTIMENT_CLASS[news.sentiment_label] ?? SENTIMENT_CLASS.neutral;

  return (
    <article
      className="rounded-md border border-muted/30 bg-white/[0.02] p-4 text-sm leading-relaxed"
      data-news-id={news.news_id}
    >
      <header className="mb-3 flex flex-wrap items-baseline justify-between gap-3">
        <h3 className="font-semibold tracking-tight">
          <a
            href={news.url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-accent hover:underline"
          >
            {hostFromUrl(news.url)}
          </a>
        </h3>
        <FreshnessBadge iso={news.summarized_at} />
      </header>

      {lowConfidence ? (
        <p className="mb-3 rounded border border-amber-500/40 bg-amber-500/[0.05] px-2 py-1 text-[11px] text-amber-300">
          Low confidence. Verify manually before relying on this context.
        </p>
      ) : null}

      <p className="text-fg/90">{news.summary}</p>

      <dl className="mt-4 space-y-3 text-xs">
        <div className="flex items-center gap-2">
          <dt className="text-[10px] uppercase tracking-widest text-muted">Sentiment</dt>
          <dd>
            <span
              className={`rounded border px-2 py-0.5 text-[10px] uppercase tracking-widest ${sentimentClass}`}
              data-sentiment={news.sentiment_label}
            >
              {SENTIMENT_LABEL[news.sentiment_label] ?? "Neutral"}
            </span>
          </dd>
        </div>

        {news.affected_tickers.length > 0 ? (
          <div>
            <dt className="text-[10px] uppercase tracking-widest text-muted">Affected tickers</dt>
            <dd className="mt-0.5 font-mono text-fg/90">{news.affected_tickers.join(", ")}</dd>
          </div>
        ) : null}

        {news.caveats.length > 0 ? (
          <div>
            <dt className="text-[10px] uppercase tracking-widest text-muted">Caveats</dt>
            <dd className="mt-0.5">
              <ul className="list-disc space-y-0.5 pl-4 text-fg/90">
                {news.caveats.map((caveat, index) => (
                  <li key={`${caveat}-${index}`}>{caveat}</li>
                ))}
              </ul>
            </dd>
          </div>
        ) : null}

        <div className="flex items-center justify-between gap-2 text-[10px] text-muted">
          <span>{QUALITY_LABEL[news.source_quality] ?? QUALITY_LABEL.unknown}</span>
          <span className="tabular-nums">confidence {news.confidence.toFixed(2)}</span>
        </div>
      </dl>
    </article>
  );
}

function hostFromUrl(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}
