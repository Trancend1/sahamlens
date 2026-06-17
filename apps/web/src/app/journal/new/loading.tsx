export default function Loading() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <div className="animate-pulse">
        <div className="h-3 w-48 rounded bg-white/5" />
        <div className="mt-2 h-8 w-56 rounded bg-white/5" />
        <div className="mt-3 h-4 w-full max-w-md rounded bg-white/5" />
      </div>
      <div className="flex flex-col gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="animate-pulse space-y-2">
            <div className="h-3 w-28 rounded bg-white/5" />
            <div className="h-10 w-full rounded-md border border-muted/30 bg-white/[0.02]" />
          </div>
        ))}
        <div className="h-10 w-36 animate-pulse rounded-md bg-white/5" />
      </div>
    </main>
  );
}
