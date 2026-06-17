"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { InitStatus } from "@/app/api/runtime/status/route";

const DISMISS_KEY = "sahamlens_welcome_dismissed";

export function WelcomeBanner() {
  const [status, setStatus] = useState<InitStatus | null>(null);
  const [dismissed, setDismissed] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem(DISMISS_KEY);
    if (stored === "true") {
      setDismissed(true);
      setLoading(false);
      return;
    }
    setDismissed(false);

    let cancelled = false;
    fetch("/api/runtime/status")
      .then((r) => r.json() as Promise<InitStatus>)
      .then((d) => { if (!cancelled) setStatus(d); })
      .catch(() => { if (!cancelled) setStatus(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  if (loading || dismissed) return null;
  if (!status?.is_first_run) return null;

  return (
    <div className="rounded-md border border-blue-500/30 bg-blue-500/[0.06] px-6 py-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-blue-300">
            Selamat datang di SahamLens
          </p>
          <p className="mt-1 text-sm text-fg/80">
            Database dan data siap. Mulai dengan menambahkan saham ke watchlist
            atau impor portofolio kamu.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              href="/watchlist"
              className="rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500"
            >
              Tambah Watchlist
            </Link>
            <Link
              href="/portfolio"
              className="rounded border border-blue-500/40 px-3 py-1.5 text-xs font-medium text-blue-300 hover:bg-blue-500/10"
            >
              Impor Portofolio
            </Link>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            localStorage.setItem(DISMISS_KEY, "true");
            setDismissed(true);
          }}
          className="shrink-0 text-sm text-muted hover:text-fg"
          aria-label="Tutup"
        >
          &times;
        </button>
      </div>
    </div>
  );
}
