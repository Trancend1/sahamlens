import { EarningsDashboard } from "@/components/EarningsDashboard";
import {
  fetchEarningsEvents,
  fetchEarningsSummaries,
  type EarningsEvent,
  type EarningsSummary,
} from "@/lib/earnings";
import { normalizeRuntimeError, type RuntimeErrorInfo } from "@/lib/pythonRunner";
import {
  archiveEarningsEventAction,
  createEarningsEventAction,
  generateEarningsSummaryAction,
  updateEarningsNotesAction,
} from "./actions";

export const dynamic = "force-dynamic";

export default async function EarningsPage() {
  let events: EarningsEvent[] = [];
  let summaries: EarningsSummary[] = [];
  let error: RuntimeErrorInfo | null = null;

  try {
    [events, summaries] = await Promise.all([
      fetchEarningsEvents(),
      fetchEarningsSummaries(),
    ]);
  } catch (err) {
    error = normalizeRuntimeError(err);
  }

  return (
    <EarningsDashboard
      events={events}
      summaries={summaries}
      error={error}
      actions={{
        createEvent: createEarningsEventAction,
        generateSummary: generateEarningsSummaryAction,
        updateNotes: updateEarningsNotesAction,
        archiveEvent: archiveEarningsEventAction,
      }}
    />
  );
}
