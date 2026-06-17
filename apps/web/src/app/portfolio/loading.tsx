export default function Loading() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 px-6 py-10">
      <div className="animate-pulse">
        <div className="h-3 w-40 rounded bg-white/5" />
        <div className="mt-2 h-8 w-40 rounded bg-white/5" />
        <div className="mt-3 h-4 w-72 rounded bg-white/5" />
      </div>
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-4 border-b border-muted/20 pb-2">
          <div className="h-3 w-20 rounded bg-white/5" />
          <div className="h-3 w-20 rounded bg-white/5" />
          <div className="h-3 w-24 rounded bg-white/5" />
          <div className="h-3 w-16 rounded bg-white/5" />
        </div>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-md border border-muted/30 bg-white/[0.02] p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-5 w-16 rounded bg-white/5" />
                <div className="h-4 w-20 rounded bg-white/5" />
                <div className="h-4 w-24 rounded bg-white/5" />
              </div>
              <div className="h-4 w-16 rounded bg-white/5" />
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
