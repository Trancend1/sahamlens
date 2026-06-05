import Link from "next/link";
import { DataTableWrapper } from "@/components/ui/DataTableWrapper";
import { EmptyState } from "@/components/ui/EmptyState";
import { RuntimeErrorState } from "@/components/ui/RuntimeErrorState";
import type {
  EarningsConfidenceStatus,
  EarningsEvent,
  EarningsEventStatus,
  EarningsSourceType,
  EarningsSummary,
} from "@/lib/earnings";
import type { RuntimeErrorInfo } from "@/lib/pythonRunner";

type FormAction = (formData: FormData) => Promise<void>;

interface EarningsActions {
  createEvent?: FormAction;
  generateSummary?: FormAction;
  updateNotes?: FormAction;
  archiveEvent?: FormAction;
}

interface Props {
  events: EarningsEvent[];
  summaries: EarningsSummary[];
  error: RuntimeErrorInfo | null;
  actions?: EarningsActions;
}

const SOURCE_TYPE_LABEL: Record<EarningsSourceType, string> = {
  manual: "Manual",
  local_note: "Local note",
  imported_file: "Imported file",
  unknown: "Unknown",
};

const EVENT_STATUS_LABEL: Record<EarningsEventStatus, string> = {
  planned: "Planned",
  reported: "Reported",
  summarized: "Summarized",
  archived: "Archived",
};

const CONFIDENCE_LABEL: Record<EarningsConfidenceStatus, string> = {
  manual_only: "manual_only",
  partial_local_data: "partial_local_data",
  insufficient_data: "insufficient_data",
};

export function EarningsDashboard({
  events,
  summaries,
  error,
  actions = {},
}: Props): React.ReactElement {
  const summariesByEvent = new Map(summaries.map((item) => [item.earnings_event_id, item]));
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">
          <Link href="/" className="hover:text-fg">
            SahamLens
          </Link>{" "}
          / V1-S6
        </p>
        <h1 className="mt-1 text-3xl font-semibold">Earnings</h1>
        <p className="mt-2 max-w-3xl text-sm text-muted">
          Track earnings events manually and generate caveated summaries for post-event
          review. Summaries are based on available local/manual data, not predictions or
          instructions.
        </p>
      </header>

      {error ? <ErrorPanel error={error} /> : null}
      {!error ? (
        <>
          <CreateEventForm actions={actions} />
          <EventsSection events={events} summariesByEvent={summariesByEvent} actions={actions} />
        </>
      ) : null}
    </main>
  );
}

function CreateEventForm({ actions }: { actions: EarningsActions }): React.ReactElement {
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <h2 className="text-sm font-medium">Create Earnings Event</h2>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Add a manual event with notes or source context. The summary workflow uses this
        local input for post-event review.
      </p>
      <form action={actions.createEvent} className="mt-4 grid gap-3 lg:grid-cols-[1fr_1fr_1fr_1fr]">
        <label className="grid gap-1 text-xs uppercase tracking-widest text-muted">
          Ticker
          <input
            name="ticker"
            className="rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg"
            placeholder="BBCA"
            required
          />
        </label>
        <label className="grid gap-1 text-xs uppercase tracking-widest text-muted">
          Period
          <input
            name="period"
            className="rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg"
            placeholder="2026-Q2"
            required
          />
        </label>
        <label className="grid gap-1 text-xs uppercase tracking-widest text-muted">
          Event date
          <input
            name="eventDate"
            type="date"
            className="rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg"
            required
          />
        </label>
        <label className="grid gap-1 text-xs uppercase tracking-widest text-muted">
          Source type
          <select
            name="sourceType"
            className="rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg"
            defaultValue="manual"
          >
            <option value="manual">Manual</option>
            <option value="local_note">Local note</option>
            <option value="imported_file">Imported file</option>
            <option value="unknown">Unknown</option>
          </select>
        </label>
        <label className="grid gap-1 text-xs uppercase tracking-widest text-muted lg:col-span-2">
          Source reference
          <input
            name="sourceRef"
            className="rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg"
            placeholder="Owner note, file name, or meeting note"
          />
        </label>
        <label className="grid gap-1 text-xs uppercase tracking-widest text-muted lg:col-span-2">
          Notes
          <textarea
            name="notes"
            rows={4}
            className="rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg"
            placeholder="Manual notes and source context for post-event review."
          />
        </label>
        <div className="lg:col-span-4">
          <button className="rounded border border-accent/40 px-3 py-2 text-sm text-accent hover:bg-accent/10">
            Add earnings event
          </button>
        </div>
      </form>
    </section>
  );
}

function EventsSection({
  events,
  summariesByEvent,
  actions,
}: {
  events: EarningsEvent[];
  summariesByEvent: Map<string, EarningsSummary>;
  actions: EarningsActions;
}): React.ReactElement {
  return (
    <section className="grid gap-3">
      <h2 className="text-sm font-medium">Earnings Events</h2>
      {events.length === 0 ? (
        <EmptyState
          title="No earnings events yet"
          description="Add an earnings event manually to track notes and generate a post-event summary later."
          actionLabel="Add earnings event"
        />
      ) : (
        <div className="grid gap-4">
          <DataTableWrapper>
            <table className="w-full min-w-[860px] text-left text-sm">
              <thead className="border-b border-muted/20 text-xs uppercase tracking-widest text-muted">
                <tr>
                  <th className="px-4 py-3">Ticker</th>
                  <th className="px-4 py-3">Period</th>
                  <th className="px-4 py-3">Event Date</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Updated</th>
                  <th className="px-4 py-3">Summary</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => {
                  const summary = summariesByEvent.get(event.id);
                  return (
                    <tr key={event.id} className="border-b border-muted/10 align-top last:border-b-0">
                      <td className="px-4 py-4 font-mono">{event.ticker}</td>
                      <td className="px-4 py-4">{event.period}</td>
                      <td className="px-4 py-4">{formatDateOnly(event.event_date)}</td>
                      <td className="px-4 py-4">
                        <Badge label={EVENT_STATUS_LABEL[event.status]} />
                      </td>
                      <td className="px-4 py-4">
                        <p>{SOURCE_TYPE_LABEL[event.source_type]}</p>
                        {event.source_ref ? (
                          <p className="mt-1 max-w-xs text-xs text-muted">{event.source_ref}</p>
                        ) : null}
                      </td>
                      <td className="px-4 py-4">{formatDate(event.updated_at)}</td>
                      <td className="px-4 py-4">
                        {summary ? (
                          <Badge label="Ready" />
                        ) : (
                          <form action={actions.generateSummary}>
                            <input type="hidden" name="eventId" value={event.id} />
                            <button className="rounded border border-accent/40 px-2 py-1 text-xs text-accent">
                              Generate summary
                            </button>
                          </form>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </DataTableWrapper>
          {events.map((event) => (
            <EventDetail
              key={event.id}
              event={event}
              summary={summariesByEvent.get(event.id) ?? null}
              actions={actions}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function EventDetail({
  event,
  summary,
  actions,
}: {
  event: EarningsEvent;
  summary: EarningsSummary | null;
  actions: EarningsActions;
}): React.ReactElement {
  return (
    <article className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-medium">
            {event.ticker} / {event.period}
          </p>
          <p className="mt-1 text-xs text-muted">
            Event date {formatDateOnly(event.event_date)} / {SOURCE_TYPE_LABEL[event.source_type]}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge label={EVENT_STATUS_LABEL[event.status]} />
          {summary ? <Badge label={CONFIDENCE_LABEL[summary.confidence_status]} /> : null}
        </div>
      </div>
      {event.notes ? <p className="mt-3 text-sm text-fg">{event.notes}</p> : null}
      {summary ? (
        <SummaryDetail summary={summary} />
      ) : (
        <div className="mt-4">
          <EmptyState
            title="No summary generated yet"
            description="Generate a summary from the manual notes and available local data for this event."
            actionLabel="Generate summary"
          />
          <form action={actions.generateSummary} className="mt-3">
            <input type="hidden" name="eventId" value={event.id} />
            <button className="rounded border border-accent/40 px-3 py-1.5 text-sm text-accent hover:bg-accent/10">
              Generate summary
            </button>
          </form>
        </div>
      )}
      <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]">
        <form action={actions.updateNotes} className="grid gap-2">
          <input type="hidden" name="eventId" value={event.id} />
          <label className="text-xs uppercase tracking-widest text-muted">
            Update notes
            <textarea
              name="notes"
              rows={3}
              className="mt-1 w-full rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg"
              defaultValue={event.notes ?? ""}
            />
          </label>
          <button className="w-fit rounded border border-muted/40 px-3 py-1.5 text-sm text-muted hover:bg-white/[0.03]">
            Update notes
          </button>
        </form>
        {event.status !== "archived" ? (
          <form action={actions.archiveEvent} className="self-end">
            <input type="hidden" name="eventId" value={event.id} />
            <button className="rounded border border-muted/40 px-3 py-1.5 text-sm text-muted hover:bg-white/[0.03]">
              Archive event
            </button>
          </form>
        ) : null}
      </div>
    </article>
  );
}

function SummaryDetail({ summary }: { summary: EarningsSummary }): React.ReactElement {
  return (
    <section className="mt-4 rounded-md border border-emerald-500/30 bg-emerald-500/[0.04] p-4">
      <p className="text-sm font-medium">Summary</p>
      <p className="mt-2 text-sm">{summary.summary_text}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-widest text-muted">Caveats</p>
          <ul className="mt-2 grid gap-1 text-sm text-muted">
            {summary.caveats.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs uppercase tracking-widest text-muted">Input snapshot</p>
          <pre className="mt-2 max-h-48 overflow-auto rounded border border-muted/20 bg-bg p-3 text-xs text-muted">
            {JSON.stringify(summary.input_snapshot, null, 2)}
          </pre>
        </div>
      </div>
      <p className="mt-3 text-xs text-muted">
        Generated {formatDate(summary.generated_at)} / confidence{" "}
        {CONFIDENCE_LABEL[summary.confidence_status]}
      </p>
    </section>
  );
}

function ErrorPanel({ error }: { error: RuntimeErrorInfo }): React.ReactElement {
  const isSchemaError = error.code === "missing_table" || error.code === "schema_stale";
  return (
    <RuntimeErrorState
      title={isSchemaError ? "Migration required" : "Earnings could not be loaded"}
      message={error.message}
      details={error.details}
      recommendedCommand={
        error.recommended_command ?? "uv run python -m scripts.runtime status --json"
      }
    />
  );
}

function Badge({ label }: { label: string }): React.ReactElement {
  return (
    <span className="rounded border border-muted/40 px-2 py-1 text-xs uppercase tracking-widest text-muted">
      {label}
    </span>
  );
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatDateOnly(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
  }).format(new Date(value));
}
