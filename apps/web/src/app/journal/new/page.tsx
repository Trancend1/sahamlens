import TradePlanForm from "@/components/TradePlanForm";

export default function NewJournalPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">SahamLens · Journal</p>
        <h1 className="mt-1 text-3xl font-semibold">Trade Plan Baru</h1>
        <p className="mt-2 text-sm text-muted">
          Isi semua field sebelum masuk pasar. Kalkulator posisi otomatis dari harga entry, stop,
          dan risk budget.
        </p>
      </header>

      <TradePlanForm />

      <footer className="text-xs text-muted">
        Personal learning & analysis tool. Bukan investment advice. AI explains, user decides.
      </footer>
    </main>
  );
}
