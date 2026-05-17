export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 px-6">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">SahamLens</p>
        <h1 className="mt-1 text-3xl font-semibold">Phase 0 — Foundations</h1>
      </header>

      <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm leading-relaxed">
        <p>
          Repo skeleton hidup. Belum ada fitur — sprint berikutnya: ingestion harga (yfinance →
          DuckDB) + watchlist CRUD.
        </p>
        <p className="mt-3 text-muted">
          Personal learning & analysis tool. Bukan investment advice. Lihat <code>DISCLAIMER.md</code>.
        </p>
      </section>

      <footer className="text-xs text-muted">
        AI explains, user decides. No buy/sell signal, no auto-execute, no broker credential.
      </footer>
    </main>
  );
}
