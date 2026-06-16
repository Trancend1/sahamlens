export default function Loading() {
  return (
    <div className="flex flex-col gap-6">
      <div className="animate-pulse space-y-3">
        <div className="h-3 w-40 rounded bg-white/5" />
        <div className="h-4 w-72 rounded bg-white/5" />
        <div className="grid gap-3 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 rounded-md border border-muted/30 bg-white/[0.02] p-4">
              <div className="h-4 w-24 rounded bg-white/5" />
              <div className="mt-2 h-3 w-40 rounded bg-white/5" />
              <div className="mt-2 h-3 w-32 rounded bg-white/5" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
