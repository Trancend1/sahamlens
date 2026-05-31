import { DataQualityDashboard } from "@/components/DataQualityDashboard";
import { fetchDataQualityOverview, type DataQualityOverview } from "@/lib/dataQuality";

export const dynamic = "force-dynamic";

export default async function DataQualityPage() {
  let overview: DataQualityOverview | null = null;
  let error: string | null = null;

  try {
    overview = await fetchDataQualityOverview();
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  return <DataQualityDashboard overview={overview} error={error} />;
}
