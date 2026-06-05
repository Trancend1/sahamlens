import Link from "next/link";

const NAV = [
  { href: "/data-quality", label: "Data Quality", desc: "Check data readiness and provider health." },
  { href: "/screener", label: "Screener", desc: "Run transparent filters with confidence caveats." },
  { href: "/journal/weekly-review", label: "Weekly Review", desc: "Review journal consistency and follow-ups." },
  { href: "/strategy-rules", label: "Strategy Rules", desc: "Evaluate named rule discipline checks." },
  { href: "/alerts", label: "Alerts", desc: "Review local rule conditions and false-positive feedback." },
  { href: "/earnings", label: "Earnings", desc: "Track manual events and caveated post-event summaries." },
  { href: "/watchlist", label: "Watchlist", desc: "Track the tickers you review regularly." },
  { href: "/journal", label: "Trade Journal", desc: "Record plans, risk, thesis, and emotions." },
  { href: "/portfolio", label: "Portfolio", desc: "Review local positions with available prices." },
];

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">SahamLens</p>
        <h1 className="mt-1 text-3xl font-semibold">Dashboard</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Check data readiness, review your watchlist, and use local decision-support tools
          without treating the app as a trading signal.
        </p>
      </header>

      <nav className="grid gap-3 sm:grid-cols-2">
        {NAV.map((n) => (
          <Link
            key={n.href}
            href={n.href}
            className="rounded-md border border-muted/30 bg-white/[0.02] p-5 hover:border-accent/40 hover:bg-accent/5"
          >
            <p className="text-sm font-medium text-fg">{n.label}</p>
            <p className="mt-1 text-xs text-muted">{n.desc}</p>
          </Link>
        ))}
      </nav>

    </main>
  );
}
