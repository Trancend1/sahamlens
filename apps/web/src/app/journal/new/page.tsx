import Link from "next/link";
import TradePlanForm from "@/components/TradePlanForm";

export default function NewJournalPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <header>
        <div className="flex items-center gap-3">
          <p className="text-sm uppercase tracking-widest text-muted">SahamLens · Journal</p>
          <Link href="/journal" className="text-xs text-accent hover:underline">
            ← Journal
          </Link>
        </div>
        <h1 className="mt-1 text-3xl font-semibold">Trade Plan Baru</h1>
        <p className="mt-2 text-sm text-muted">
          Isi semua field sebelum masuk pasar. Kalkulator posisi otomatis dari harga entry, stop,
          dan risk budget.
        </p>
      </header>

      <TradePlanForm />

    </main>
  );
}
