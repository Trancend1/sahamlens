import { checkFreshness } from "@/lib/runtime";
import { OperationsTable } from "@/components/OperationsTable";

export const dynamic = "force-dynamic";

export default async function ProvidersPage() {
  let report;
  try {
    report = await checkFreshness();
  } catch {
    report = {
      fresh_count: 0,
      stale_count: 0,
      total_count: 0,
      has_stale: false,
      stale_types: [],
      records: [],
    };
  }

  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted">
        Monitor and run data operations. Status shows when each data type was last refreshed.
      </p>
      <OperationsTable report={report} />
    </div>
  );
}
