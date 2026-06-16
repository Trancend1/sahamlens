import type { ReactNode } from "react";
import Link from "next/link";

const TABS = [
  { href: "/operations/providers", label: "Providers" },
  { href: "/operations/health", label: "Health" },
  { href: "/operations/hermes", label: "Hermes" },
  { href: "/operations/config", label: "Config" },
];

export default function OperationsLayout({ children }: { children: ReactNode }) {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">SahamLens / Operations</p>
        <h1 className="mt-1 text-3xl font-semibold">Operations</h1>
      </header>

      <nav className="flex gap-1 border-b border-muted/20">
        {TABS.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            className="rounded-t px-4 py-2 text-sm font-medium text-muted transition-colors hover:text-fg aria-[current=page]:border-b-2 aria-[current=page]:border-accent aria-[current=page]:text-accent"
          >
            {tab.label}
          </Link>
        ))}
      </nav>

      {children}
    </main>
  );
}
