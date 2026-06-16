export default function Loading() {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
      <div className="animate-pulse">
        <div className="h-3 w-44 rounded bg-white/5" />
        <div className="mt-2 h-8 w-36 rounded bg-white/5" />
        <div className="mt-3 h-4 w-96 rounded bg-white/5" />
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="h-72 animate-pulse rounded-md border border-muted/30 bg-white/[0.02]" />
          <div className="grid grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-20 animate-pulse rounded-md border border-muted/30 bg-white/[0.02]" />
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-4">
          <div className="h-40 animate-pulse rounded-md border border-muted/30 bg-white/[0.02]" />
          <div className="h-52 animate-pulse rounded-md border border-muted/30 bg-white/[0.02]" />
          <div className="h-36 animate-pulse rounded-md border border-muted/30 bg-white/[0.02]" />
        </div>
      </div>
    </main>
  );
}
