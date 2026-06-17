export default function Loading() {
  return (
    <div className="flex flex-col gap-6">
      <div className="animate-pulse space-y-3">
        <div className="h-3 w-28 rounded bg-white/5" />
        <div className="h-4 w-48 rounded bg-white/5" />
        <div className="flex flex-col gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-md border border-muted/30 bg-white/[0.02] p-4">
              <div className="flex items-center justify-between">
                <div className="h-4 w-28 rounded bg-white/5" />
                <div className="h-6 w-12 rounded bg-white/5" />
              </div>
              <div className="mt-2 h-3 w-3/4 rounded bg-white/5" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
