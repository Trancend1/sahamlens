import { runPython, toRuntimeFetchError } from "./pythonRunner";

export type EarningsSourceType = "manual" | "local_note" | "imported_file" | "unknown";
export type EarningsEventStatus = "planned" | "reported" | "summarized" | "archived";
export type EarningsConfidenceStatus =
  | "manual_only"
  | "partial_local_data"
  | "insufficient_data";

export interface EarningsEvent {
  id: string;
  ticker: string;
  period: string;
  event_date: string;
  source_type: EarningsSourceType;
  source_ref: string | null;
  status: EarningsEventStatus;
  created_at: string;
  updated_at: string;
  notes: string | null;
}

export interface EarningsSummary {
  id: string;
  earnings_event_id: string;
  generated_at: string;
  summary_text: string;
  caveats: string[];
  input_snapshot: Record<string, unknown>;
  confidence_status: EarningsConfidenceStatus;
}

interface EarningsCliResponse<TItem = unknown, TItems = unknown> {
  ok: boolean;
  status: string;
  item?: TItem;
  items?: TItems[];
  warnings: unknown[];
  errors: unknown[];
  recommended_commands: string[];
}

interface CreateEarningsEventInput {
  ticker: string;
  period: string;
  eventDate: string;
  sourceType: EarningsSourceType;
  sourceRef?: string;
  notes?: string;
}

const TIMEOUT_MS = 30_000;

export async function fetchEarningsEvents(): Promise<EarningsEvent[]> {
  try {
    const { data } = await runPython<EarningsCliResponse<unknown, EarningsEvent>>(
      "scripts.earnings",
      {
        args: ["--json", "events", "list"],
        timeoutMs: TIMEOUT_MS,
      },
    );
    return data.items ?? [];
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

export async function createEarningsEvent(
  input: CreateEarningsEventInput,
): Promise<EarningsEvent | null> {
  const args = [
    "--json",
    "events",
    "create",
    "--ticker",
    input.ticker,
    "--period",
    input.period,
    "--event-date",
    input.eventDate,
    "--source-type",
    input.sourceType,
  ];
  if (input.sourceRef) {
    args.push("--source-ref", input.sourceRef);
  }
  if (input.notes) {
    args.push("--notes", input.notes);
  }
  try {
    const { data } = await runPython<EarningsCliResponse<EarningsEvent>>("scripts.earnings", {
      args,
      timeoutMs: TIMEOUT_MS,
    });
    return data.item ?? null;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

export async function updateEarningsEventNotes(
  eventId: string,
  notes: string,
): Promise<EarningsEvent | null> {
  try {
    const { data } = await runPython<EarningsCliResponse<EarningsEvent>>("scripts.earnings", {
      args: ["--json", "events", "update-notes", "--event-id", eventId, "--notes", notes],
      timeoutMs: TIMEOUT_MS,
    });
    return data.item ?? null;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

export async function archiveEarningsEvent(eventId: string): Promise<EarningsEvent | null> {
  try {
    const { data } = await runPython<EarningsCliResponse<EarningsEvent>>("scripts.earnings", {
      args: ["--json", "events", "archive", "--event-id", eventId],
      timeoutMs: TIMEOUT_MS,
    });
    return data.item ?? null;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

export async function generateEarningsSummary(
  eventId: string,
): Promise<EarningsSummary | null> {
  try {
    const { data } = await runPython<EarningsCliResponse<EarningsSummary>>(
      "scripts.earnings",
      {
        args: ["--json", "summary", "generate", "--event-id", eventId],
        timeoutMs: TIMEOUT_MS,
      },
    );
    return data.item ?? null;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

export async function fetchEarningsSummaries(): Promise<EarningsSummary[]> {
  try {
    const { data } = await runPython<EarningsCliResponse<unknown, EarningsSummary>>(
      "scripts.earnings",
      {
        args: ["--json", "summaries", "list"],
        timeoutMs: TIMEOUT_MS,
      },
    );
    return data.items ?? [];
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}
