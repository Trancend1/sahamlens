import Link from "next/link";

const NAV = [
  { href: "/data-quality", label: "Data Quality", desc: "Provider health & freshness" },
  { href: "/screener", label: "Screener", desc: "Transparent filters" },
  { href: "/journal/weekly-review", label: "Weekly Review", desc: "Journal behavior review" },
  { href: "/strategy-rules", label: "Strategy Rules", desc: "Named journal checks" },
  { href: "/watchlist", label: "Watchlist", desc: "Ticker yang diikuti" },
  { href: "/journal", label: "Trade Journal", desc: "Plan, review, AI kritik" },
  { href: "/portfolio", label: "Portfolio", desc: "Posisi & P&L aktual" },
];

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 px-6">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">SahamLens</p>
        <h1 className="mt-1 text-3xl font-semibold">Dashboard</h1>
      </header>

      <nav className="grid grid-cols-2 gap-4">
        {NAV.map((n) => (
          <Link
            key={n.href}
            href={n.href}
            className="rounded-md border border-muted/30 bg-white/[0.02] p-4 hover:border-accent/40 hover:bg-accent/5"
          >
            <p className="text-sm font-medium text-fg">{n.label}</p>
            <p className="mt-1 text-xs text-muted">{n.desc}</p>
          </Link>
        ))}
      </nav>

    </main>
  );
}
