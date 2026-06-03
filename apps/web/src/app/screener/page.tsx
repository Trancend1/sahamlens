import { ScreenerDashboard } from "@/components/ScreenerDashboard";
import { fetchScreenerRun, type ScreenerRun } from "@/lib/screener";

export const dynamic = "force-dynamic";

export default async function ScreenerPage() {
  let run: ScreenerRun | null = null;
  let error: string | null = null;

  try {
    run = await fetchScreenerRun();
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  return <ScreenerDashboard run={run} error={error} />;
}
