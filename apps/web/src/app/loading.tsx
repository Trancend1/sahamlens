export default function Loading() {
  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-6 py-10">
      <div className="animate-pulse">
        <div className="h-3 w-32 rounded bg-white/5" />
        <div className="mt-2 h-8 w-56 rounded bg-white/5" />
        <div className="mt-3 h-4 w-80 rounded bg-white/5" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-md border border-muted/30 bg-white/[0.02] p-5">
            <div className="h-4 w-28 rounded bg-white/5" />
            <div className="mt-2 h-3 w-48 rounded bg-white/5" />
          </div>
        ))}
      </div>
    </div>
  );
}
