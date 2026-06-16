"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col items-center justify-center gap-4 px-6 py-10">
      <p className="text-sm uppercase tracking-widest text-muted">SahamLens / Screener</p>
      <h2 className="text-xl font-semibold">Something went wrong</h2>
      <p className="max-w-md text-center text-sm text-muted">
        An unexpected error occurred. This is usually a temporary issue.
      </p>
      <button
        onClick={() => reset()}
        className="rounded-md bg-accent px-4 py-2 text-xs font-medium text-white hover:opacity-90"
      >
        Try again
      </button>
    </main>
  );
}
