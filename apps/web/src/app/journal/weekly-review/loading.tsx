export default function Loading() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-6 py-10">
      <div className="animate-pulse">
        <div className="h-3 w-52 rounded bg-white/5" />
        <div className="mt-2 h-8 w-44 rounded bg-white/5" />
        <div className="mt-3 h-4 w-80 rounded bg-white/5" />
      </div>
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="animate-pulse rounded-md border border-muted/30 bg-white/[0.02] p-5">
          <div className="flex items-center justify-between">
            <div className="h-5 w-32 rounded bg-white/5" />
            <div className="h-4 w-20 rounded bg-white/5" />
          </div>
          <div className="mt-3 space-y-2">
            <div className="h-3 w-full rounded bg-white/5" />
            <div className="h-3 w-3/4 rounded bg-white/5" />
          </div>
          <div className="mt-3 flex gap-2">
            <div className="h-6 w-16 rounded bg-white/5" />
            <div className="h-6 w-20 rounded bg-white/5" />
          </div>
        </div>
      ))}
    </main>
  );
}
