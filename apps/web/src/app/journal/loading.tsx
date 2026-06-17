export default function Loading() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-6 py-10">
      <div className="animate-pulse">
        <div className="h-3 w-40 rounded bg-white/5" />
        <div className="mt-2 h-8 w-48 rounded bg-white/5" />
        <div className="mt-3 h-4 w-72 rounded bg-white/5" />
      </div>
      <div className="flex gap-2">
        <div className="h-8 w-24 animate-pulse rounded bg-white/5" />
        <div className="h-8 w-24 animate-pulse rounded bg-white/5" />
        <div className="h-8 w-28 animate-pulse rounded bg-white/5" />
      </div>
      <div className="flex flex-col gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-md border border-muted/30 bg-white/[0.02] p-5">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="h-5 w-24 rounded bg-white/5" />
                <div className="h-3 w-48 rounded bg-white/5" />
                <div className="h-3 w-36 rounded bg-white/5" />
              </div>
              <div className="h-6 w-16 rounded bg-white/5" />
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
