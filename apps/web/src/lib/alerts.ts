import { runPython, toRuntimeFetchError } from "./pythonRunner";

export type AlertRuleType = "price_above" | "price_below" | "volume_above";
export type AlertDefinitionStatus = "active" | "paused" | "archived";
export type AlertEventStatus =
  | "new"
  | "acknowledged"
  | "dismissed"
  | "marked_false_positive"
  | "resolved";
export type AlertSeverity = "info" | "warning" | "critical";
export type AlertEvaluationStatus =
  | "success"
  | "skipped_stale_data"
  | "skipped_low_confidence"
  | "failed_provider"
  | "failed_runtime"
  | "no_match";

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  rule_type: AlertRuleType;
  ticker: string;
  parameters: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  evaluation_id: string;
  ticker: string;
  event_type: AlertRuleType;
  severity: AlertSeverity;
  title: string;
  message: string;
  status: AlertEventStatus;
  created_at: string;
  acknowledged_at: string | null;
  dismissed_at: string | null;
  false_positive_at: string | null;
  resolved_at: string | null;
  notes: string | null;
}

export interface AlertEvaluation {
  id: string;
  rule_id: string;
  ticker: string;
  evaluated_at: string;
  status: AlertEvaluationStatus;
  reason: string;
  data_freshness_status: string;
  confidence_status: string;
  matched: boolean;
  details: Record<string, unknown>;
}

export interface AlertEvaluationResult {
  evaluated_count: number;
  event_count: number;
  evaluations: AlertEvaluation[];
  events: AlertEvent[];
  warnings: string[];
}

export interface TelegramStatus {
  enabled: boolean;
  configured: boolean;
  status: "configured" | "not_configured" | "disabled";
  bot_token_configured: boolean;
  chat_id_configured: boolean;
  message: string;
}

export interface TelegramDeliveryAttempt {
  id: string;
  event_id: string;
  channel: "telegram";
  status: "disabled" | "skipped_not_configured" | "sent" | "failed";
  attempted_at: string;
  error_code: string | null;
  error_message: string | null;
  redacted_details: Record<string, unknown>;
}

export interface TelegramDeliveryResult {
  ok: boolean;
  status: "sent" | "skipped_not_configured" | "failed" | "not_found";
  event_id: string | null;
  attempt: TelegramDeliveryAttempt | null;
  warnings: Array<Record<string, unknown>>;
  errors: Array<Record<string, unknown>>;
  recommended_commands: string[];
}

interface AlertCliResponse<TItem = unknown, TItems = unknown> {
  ok: boolean;
  status: string;
  item?: TItem;
  items?: TItems[];
  warnings: unknown[];
  errors: unknown[];
  recommended_commands: string[];
}

interface CreateAlertRuleInput {
  name: string;
  description?: string;
  ruleType: AlertRuleType;
  ticker: string;
  threshold: number;
}

const TIMEOUT_MS = 30_000;

export async function fetchAlertRules(): Promise<AlertRule[]> {
  try {
    const { data } = await runPython<AlertCliResponse<unknown, AlertRule>>("scripts.alerts", {
      args: ["--json", "rules", "list"],
      timeoutMs: TIMEOUT_MS,
    });
    return data.items ?? [];
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

export async function createAlertRule(input: CreateAlertRuleInput): Promise<AlertRule | null> {
  try {
    const { data } = await runPython<AlertCliResponse<AlertRule>>("scripts.alerts", {
      args: [
        "--json",
        "rules",
        "create",
        "--name",
        input.name,
        "--description",
        input.description || input.name,
        "--rule-type",
        input.ruleType,
        "--ticker",
        input.ticker,
        "--params",
        JSON.stringify({ threshold: input.threshold }),
      ],
      timeoutMs: TIMEOUT_MS,
    });
    return data.item ?? null;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

export async function pauseAlertRule(ruleId: string): Promise<AlertRule | null> {
  return mutateAlertRule(["rules", "pause", "--rule-id", ruleId]);
}

export async function archiveAlertRule(ruleId: string): Promise<AlertRule | null> {
  return mutateAlertRule(["rules", "archive", "--rule-id", ruleId]);
}

export async function evaluateAlerts(): Promise<AlertEvaluationResult | null> {
  try {
    const { data } = await runPython<AlertCliResponse<AlertEvaluationResult>>("scripts.alerts", {
      args: ["--json", "evaluate"],
      timeoutMs: TIMEOUT_MS,
    });
    return data.item ?? null;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

export async function fetchAlertEvents(): Promise<AlertEvent[]> {
  try {
    const { data } = await runPython<AlertCliResponse<unknown, AlertEvent>>("scripts.alerts", {
      args: ["--json", "events", "list"],
      timeoutMs: TIMEOUT_MS,
    });
    return data.items ?? [];
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

export async function acknowledgeAlertEvent(eventId: string): Promise<AlertEvent | null> {
  return mutateAlertEvent(["events", "acknowledge", "--event-id", eventId]);
}

export async function dismissAlertEvent(eventId: string): Promise<AlertEvent | null> {
  return mutateAlertEvent(["events", "dismiss", "--event-id", eventId]);
}

export async function markAlertEventFalsePositive(eventId: string): Promise<AlertEvent | null> {
  return mutateAlertEvent(["events", "mark-false-positive", "--event-id", eventId]);
}

export async function fetchTelegramStatus(): Promise<TelegramStatus> {
  try {
    const { data } = await runPython<AlertCliResponse<TelegramStatus>>("scripts.alerts", {
      args: ["--json", "telegram", "status"],
      timeoutMs: TIMEOUT_MS,
    });
    return (
      data.item ?? {
        enabled: false,
        configured: false,
        status: "not_configured",
        bot_token_configured: false,
        chat_id_configured: false,
        message: "Telegram delivery is optional and not configured.",
      }
    );
  } catch {
    return {
      enabled: false,
      configured: false,
      status: "not_configured",
      bot_token_configured: false,
      chat_id_configured: false,
      message: "Telegram delivery is optional and not configured.",
    };
  }
}

export async function sendAlertEventToTelegram(
  eventId: string,
): Promise<TelegramDeliveryResult | null> {
  try {
    const { data } = await runPython<AlertCliResponse<TelegramDeliveryResult>>(
      "scripts.alerts",
      {
        args: ["--json", "telegram", "send", "--event-id", eventId],
        timeoutMs: TIMEOUT_MS,
      },
    );
    return data.item ?? null;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

async function mutateAlertRule(args: string[]): Promise<AlertRule | null> {
  try {
    const { data } = await runPython<AlertCliResponse<AlertRule>>("scripts.alerts", {
      args: ["--json", ...args],
      timeoutMs: TIMEOUT_MS,
    });
    return data.item ?? null;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}

async function mutateAlertEvent(args: string[]): Promise<AlertEvent | null> {
  try {
    const { data } = await runPython<AlertCliResponse<AlertEvent>>("scripts.alerts", {
      args: ["--json", ...args],
      timeoutMs: TIMEOUT_MS,
    });
    return data.item ?? null;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}
