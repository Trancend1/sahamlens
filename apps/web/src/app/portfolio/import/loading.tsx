export default function Loading() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <div className="animate-pulse">
        <div className="h-3 w-44 rounded bg-white/5" />
        <div className="mt-2 h-8 w-48 rounded bg-white/5" />
        <div className="mt-3 h-4 w-full max-w-md rounded bg-white/5" />
      </div>
      <div className="animate-pulse rounded-md border border-muted/30 bg-white/[0.02] p-8">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 rounded bg-white/5" />
          <div className="h-4 w-36 rounded bg-white/5" />
          <div className="h-10 w-40 rounded border border-muted/30 bg-white/[0.02]" />
        </div>
      </div>
    </main>
  );
}
