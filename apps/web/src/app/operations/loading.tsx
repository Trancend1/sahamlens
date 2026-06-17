export default function Loading() {
  return (
    <div className="flex flex-col gap-6">
      <div className="animate-pulse space-y-3">
        <div className="h-3 w-40 rounded bg-white/5" />
        <div className="h-4 w-64 rounded bg-white/5" />
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-14 rounded-md border border-muted/30 bg-white/[0.02]" />
          ))}
        </div>
      </div>
    </div>
  );
}
