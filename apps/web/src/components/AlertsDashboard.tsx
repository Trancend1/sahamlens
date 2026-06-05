import Link from "next/link";
import { DataTableWrapper } from "@/components/ui/DataTableWrapper";
import { EmptyState } from "@/components/ui/EmptyState";
import { RuntimeErrorState } from "@/components/ui/RuntimeErrorState";
import type {
  AlertEvaluationResult,
  AlertEvent,
  AlertEventStatus,
  AlertRule,
  AlertRuleType,
  TelegramStatus,
} from "@/lib/alerts";
import type { RuntimeErrorInfo } from "@/lib/pythonRunner";

type FormAction = (formData: FormData) => Promise<void>;
type VoidAction = () => Promise<void>;

interface AlertActions {
  createRule?: FormAction;
  evaluate?: VoidAction;
  pauseRule?: FormAction;
  archiveRule?: FormAction;
  acknowledgeEvent?: FormAction;
  dismissEvent?: FormAction;
  markFalsePositive?: FormAction;
  sendTelegram?: FormAction;
}

interface Props {
  rules: AlertRule[];
  events: AlertEvent[];
  telegram: TelegramStatus | null;
  error: RuntimeErrorInfo | null;
  lastEvaluation?: AlertEvaluationResult | null;
  actions?: AlertActions;
}

const RULE_TYPE_LABEL: Record<AlertRuleType, string> = {
  price_above: "price above",
  price_below: "price below",
  volume_above: "volume above",
};

const EVENT_STATUS: Record<AlertEventStatus, { label: string; className: string }> = {
  new: { label: "New", className: "border-sky-500/40 text-sky-300" },
  acknowledged: { label: "Acknowledged", className: "border-emerald-500/40 text-emerald-300" },
  dismissed: { label: "Dismissed", className: "border-muted/40 text-muted" },
  marked_false_positive: {
    label: "False Positive",
    className: "border-amber-500/40 text-amber-300",
  },
  resolved: { label: "Resolved", className: "border-emerald-500/40 text-emerald-300" },
};

export function AlertsDashboard({
  rules,
  events,
  telegram,
  error,
  lastEvaluation = null,
  actions = {},
}: Props): React.ReactElement {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">
          <Link href="/" className="hover:text-fg">
            SahamLens
          </Link>{" "}
          / V1-S6
        </p>
        <h1 className="mt-1 text-3xl font-semibold">Alerts</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Review local alert rules and matched conditions. Alerts are decision-support events
          based on available local data, not trading instructions.
        </p>
      </header>

      {error ? <ErrorPanel error={error} /> : null}
      {!error ? (
        <>
          <ManualEvaluation actions={actions} lastEvaluation={lastEvaluation} />
          <TelegramPanel telegram={telegram} />
          <RuleCreateCard actions={actions} />
          <RulesSection rules={rules} actions={actions} />
          <EventsSection
            events={events}
            actions={actions}
            lastEvaluation={lastEvaluation}
            telegram={telegram}
          />
        </>
      ) : null}
    </main>
  );
}

function ManualEvaluation({
  actions,
  lastEvaluation,
}: {
  actions: AlertActions;
  lastEvaluation: AlertEvaluationResult | null;
}): React.ReactElement {
  const skippedCount =
    lastEvaluation?.evaluations.filter((item) =>
      ["skipped_stale_data", "skipped_low_confidence"].includes(item.status),
    ).length ?? 0;
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-medium">Manual Evaluation</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Run local rules on demand. Review freshness and confidence before using any alert
            event in your workflow.
          </p>
        </div>
        <form action={actions.evaluate}>
          <button className="rounded border border-accent/40 px-3 py-1.5 text-sm text-accent hover:bg-accent/10">
            Evaluate alerts
          </button>
        </form>
      </div>
      {lastEvaluation ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <Metric label="Evaluated" value={lastEvaluation.evaluated_count} />
          <Metric label="Matched Events" value={lastEvaluation.event_count} />
          <Metric label="Skipped" value={skippedCount} />
        </div>
      ) : null}
      {skippedCount > 0 ? (
        <EmptyState
          title="Alert evaluation skipped"
          description="Some rules were skipped because local data was stale or confidence was too low. Refresh data or check Data Quality before relying on results."
          actionLabel="Open Data Quality"
          actionHref="/data-quality"
          tone="warning"
        />
      ) : null}
      {lastEvaluation && lastEvaluation.evaluated_count > 0 && lastEvaluation.event_count === 0 && skippedCount === 0 ? (
        <div className="mt-4">
          <EmptyState
            title="No alert conditions matched"
            description="Evaluation completed, but no active rule matched the available local data."
            tone="healthy"
          />
        </div>
      ) : null}
    </section>
  );
}

function TelegramPanel({ telegram }: { telegram: TelegramStatus | null }): React.ReactElement {
  if (!telegram || !telegram.configured) {
    return (
      <EmptyState
        title="Telegram delivery is disabled"
        description="Telegram delivery is optional. Local alert events remain available even when Telegram is disabled. Configure Telegram only if you want manual alert delivery outside the app."
        tone="healthy"
      />
    );
  }
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5 text-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-medium">Telegram delivery is optional</p>
          <p className="mt-2 max-w-2xl text-muted">
            {telegram.message} Local alert events remain the source of truth.
          </p>
        </div>
        <Badge label="Configured" className="border-emerald-500/40 text-emerald-300" />
      </div>
      <p className="mt-3 text-xs text-muted">
        Bot token configured: {telegram.bot_token_configured ? "yes" : "no"} / chat target configured: {telegram.chat_id_configured ? "yes" : "no"}. Secrets are not shown.
      </p>
    </section>
  );
}

function RuleCreateCard({ actions }: { actions: AlertActions }): React.ReactElement {
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <h2 className="text-sm font-medium">Create Alert Rule</h2>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Create a local threshold rule. Rules are evaluated manually and should be reviewed
        with freshness and confidence context.
      </p>
      <form action={actions.createRule} className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_1fr_1fr_auto]">
        <label className="grid gap-1 text-xs uppercase tracking-widest text-muted">
          Name
          <input name="name" className="rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg" placeholder="BBCA above threshold" required />
        </label>
        <label className="grid gap-1 text-xs uppercase tracking-widest text-muted">
          Ticker
          <input name="ticker" className="rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg" placeholder="BBCA" required />
        </label>
        <label className="grid gap-1 text-xs uppercase tracking-widest text-muted">
          Rule type
          <select name="ruleType" className="rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg" defaultValue="price_above">
            <option value="price_above">Price above</option>
            <option value="price_below">Price below</option>
            <option value="volume_above">Volume above</option>
          </select>
        </label>
        <label className="grid gap-1 text-xs uppercase tracking-widest text-muted">
          Threshold
          <input name="threshold" type="number" min="0" step="0.01" className="rounded border border-muted/30 bg-bg px-3 py-2 text-sm normal-case tracking-normal text-fg" placeholder="9000" required />
        </label>
        <button className="self-end rounded border border-accent/40 px-3 py-2 text-sm text-accent hover:bg-accent/10">
          Create alert rule
        </button>
      </form>
    </section>
  );
}

function RulesSection({
  rules,
  actions,
}: {
  rules: AlertRule[];
  actions: AlertActions;
}): React.ReactElement {
  return (
    <section className="grid gap-3">
      <h2 className="text-sm font-medium">Alert Rules</h2>
      {rules.length === 0 ? (
        <EmptyState
          title="No alert rules yet"
          description="Create a local rule to check conditions such as price or volume thresholds. Rules are evaluated manually and should be reviewed with freshness and confidence context."
          actionLabel="Create alert rule"
          command={`uv run python -m scripts.alerts --json rules create --name "BBCA above threshold" --rule-type price_above --ticker BBCA --params '{"threshold":9000}'`}
        />
      ) : (
        <DataTableWrapper>
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-muted/20 text-xs uppercase tracking-widest text-muted">
              <tr>
                <th className="px-4 py-3">Rule</th>
                <th className="px-4 py-3">Ticker</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Parameters</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.id} className="border-b border-muted/10 align-top last:border-b-0">
                  <td className="px-4 py-4">
                    <p className="font-medium">{rule.name}</p>
                    <p className="mt-1 max-w-sm text-xs text-muted">{rule.description}</p>
                    <p className="mt-1 text-xs text-muted">Updated {formatDate(rule.updated_at)}</p>
                  </td>
                  <td className="px-4 py-4 font-mono">{rule.ticker}</td>
                  <td className="px-4 py-4">{RULE_TYPE_LABEL[rule.rule_type]}</td>
                  <td className="px-4 py-4">{parameterSummary(rule.parameters)}</td>
                  <td className="px-4 py-4">
                    <RuleStatusBadge rule={rule} />
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex flex-wrap gap-2">
                      {rule.is_active && !rule.archived_at ? (
                        <form action={actions.pauseRule}>
                          <input type="hidden" name="ruleId" value={rule.id} />
                          <button className="rounded border border-amber-500/40 px-2 py-1 text-xs text-amber-300">
                            Pause rule
                          </button>
                        </form>
                      ) : null}
                      {!rule.archived_at ? (
                        <form action={actions.archiveRule}>
                          <input type="hidden" name="ruleId" value={rule.id} />
                          <button className="rounded border border-muted/40 px-2 py-1 text-xs text-muted">
                            Archive rule
                          </button>
                        </form>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataTableWrapper>
      )}
    </section>
  );
}

function EventsSection({
  events,
  actions,
  lastEvaluation,
  telegram,
}: {
  events: AlertEvent[];
  actions: AlertActions;
  lastEvaluation: AlertEvaluationResult | null;
  telegram: TelegramStatus | null;
}): React.ReactElement {
  return (
    <section className="grid gap-3">
      <h2 className="text-sm font-medium">Alert Events</h2>
      {events.length === 0 ? (
        <EmptyState
          title="No alert events yet"
          description="Run a manual evaluation after creating rules. Matching conditions will appear here for review."
          actionLabel="Evaluate alerts"
          tone={lastEvaluation?.evaluated_count ? "healthy" : "neutral"}
        />
      ) : (
        <div className="grid gap-3">
          {events.map((event) => (
            <article key={event.id} className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-medium">{event.title}</p>
                  <p className="mt-1 text-xs text-muted">
                    {event.ticker} / {RULE_TYPE_LABEL[event.event_type]} / {formatDate(event.created_at)}
                  </p>
                  <p className="mt-1 font-mono text-xs text-muted">Rule {event.rule_id}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge label={event.severity} className="border-muted/40 text-muted" />
                  <Badge
                    label={EVENT_STATUS[event.status].label}
                    className={EVENT_STATUS[event.status].className}
                  />
                </div>
              </div>
              <p className="mt-3 text-sm text-fg">{event.message}</p>
              {event.status === "marked_false_positive" ? (
                <p className="mt-3 text-sm text-amber-200">
                  Marked false positive{event.false_positive_at ? ` on ${formatDate(event.false_positive_at)}` : ""}. Marking an event as false positive helps review alert quality later.
                </p>
              ) : null}
              <div className="mt-4 flex flex-wrap gap-2">
                {event.status === "new" ? (
                  <>
                    <form action={actions.acknowledgeEvent}>
                      <input type="hidden" name="eventId" value={event.id} />
                      <button className="rounded border border-emerald-500/40 px-2 py-1 text-xs text-emerald-300">
                        Acknowledge
                      </button>
                    </form>
                    <form action={actions.dismissEvent}>
                      <input type="hidden" name="eventId" value={event.id} />
                      <button className="rounded border border-muted/40 px-2 py-1 text-xs text-muted">
                        Dismiss
                      </button>
                    </form>
                  </>
                ) : null}
                {event.status !== "marked_false_positive" && event.status !== "resolved" ? (
                  <form action={actions.markFalsePositive}>
                    <input type="hidden" name="eventId" value={event.id} />
                    <button className="rounded border border-amber-500/40 px-2 py-1 text-xs text-amber-300">
                      Mark false positive
                    </button>
                  </form>
                ) : null}
                {telegram?.configured ? (
                  <form action={actions.sendTelegram}>
                    <input type="hidden" name="eventId" value={event.id} />
                    <button className="rounded border border-sky-500/40 px-2 py-1 text-xs text-sky-300">
                      Send to Telegram
                    </button>
                  </form>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function ErrorPanel({ error }: { error: RuntimeErrorInfo }): React.ReactElement {
  const isSchemaError = error.code === "missing_table" || error.code === "schema_stale";
  return (
    <RuntimeErrorState
      title={isSchemaError ? "Migration required" : "Alerts could not be loaded"}
      message={error.message}
      details={error.details}
      recommendedCommand={error.recommended_command ?? "uv run python -m scripts.runtime status --json"}
    />
  );
}

function RuleStatusBadge({ rule }: { rule: AlertRule }): React.ReactElement {
  if (rule.archived_at) return <Badge label="Archived" className="border-muted/40 text-muted" />;
  if (!rule.is_active) return <Badge label="Paused" className="border-amber-500/40 text-amber-300" />;
  return <Badge label="Active" className="border-emerald-500/40 text-emerald-300" />;
}

function Metric({ label, value }: { label: string; value: number }): React.ReactElement {
  return (
    <div className="rounded border border-muted/20 p-3">
      <p className="text-xs uppercase tracking-widest text-muted">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}

function Badge({ label, className }: { label: string; className: string }): React.ReactElement {
  return <span className={`rounded border px-2 py-1 text-xs uppercase tracking-widest ${className}`}>{label}</span>;
}

function parameterSummary(parameters: Record<string, unknown>): string {
  const threshold = parameters.threshold;
  if (typeof threshold === "number" || typeof threshold === "string") {
    return `threshold: ${threshold}`;
  }
  return "configured";
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
