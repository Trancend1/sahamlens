import { DataQualityDashboard } from "@/components/DataQualityDashboard";
import { fetchDataQualityOverview, type DataQualityOverview } from "@/lib/dataQuality";
import { normalizeRuntimeError, type RuntimeErrorInfo } from "@/lib/pythonRunner";
import { fetchRuntimeStatus, type RuntimeStatus } from "@/lib/runtime";

export const dynamic = "force-dynamic";

export default async function DataQualityPage() {
  let overview: DataQualityOverview | null = null;
  let runtimeStatus: RuntimeStatus | null = null;
  let error: RuntimeErrorInfo | null = null;
  let runtimeError: RuntimeErrorInfo | null = null;

  try {
    runtimeStatus = await fetchRuntimeStatus();
  } catch (err) {
    runtimeError = normalizeRuntimeError(err);
  }

  try {
    overview = await fetchDataQualityOverview();
  } catch (err) {
    error = normalizeRuntimeError(err);
  }

  return (
    <DataQualityDashboard
      overview={overview}
      error={error}
      runtimeStatus={runtimeStatus}
      runtimeError={runtimeError}
    />
  );
}
