export default function Loading() {
  return (
    <div className="flex flex-col gap-6">
      <div className="animate-pulse space-y-3">
        <div className="h-3 w-32 rounded bg-white/5" />
        <div className="h-4 w-56 rounded bg-white/5" />
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 rounded-md border border-muted/30 bg-white/[0.02] p-4">
              <div className="h-3 w-3 rounded-full bg-white/5" />
              <div className="h-4 w-36 rounded bg-white/5" />
              <div className="h-3 w-24 rounded bg-white/5" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
