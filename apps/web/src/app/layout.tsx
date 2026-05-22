import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "SahamLens",
  description: "Personal trading companion. Local-first, single-user, IDX.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="id">
      <body className="flex min-h-screen flex-col font-sans antialiased">
        <main className="flex-1">{children}</main>
        <footer className="border-t border-muted/20 px-4 py-3 text-center text-xs text-muted">
          Personal learning &amp; analysis tool &middot; Bukan investment advice &middot; AI
          explains, user decides &middot;{" "}
          <span className="italic">
            Keputusan investasi sepenuhnya tanggung jawab investor
          </span>
        </footer>
      </body>
    </html>
  );
}
