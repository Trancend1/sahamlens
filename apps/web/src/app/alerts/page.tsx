import { AlertsDashboard } from "@/components/AlertsDashboard";
import {
  fetchAlertEvents,
  fetchAlertRules,
  fetchTelegramStatus,
  type AlertEvent,
  type AlertRule,
  type TelegramStatus,
} from "@/lib/alerts";
import { normalizeRuntimeError, type RuntimeErrorInfo } from "@/lib/pythonRunner";
import {
  acknowledgeAlertEventAction,
  archiveAlertRuleAction,
  createAlertRuleAction,
  dismissAlertEventAction,
  evaluateAlertsAction,
  markFalsePositiveAction,
  pauseAlertRuleAction,
  sendTelegramAction,
} from "./actions";

export const dynamic = "force-dynamic";

export default async function AlertsPage() {
  let rules: AlertRule[] = [];
  let events: AlertEvent[] = [];
  let telegram: TelegramStatus | null = null;
  let error: RuntimeErrorInfo | null = null;

  try {
    rules = await fetchAlertRules();
    events = await fetchAlertEvents();
  } catch (err) {
    error = normalizeRuntimeError(err);
  }
  telegram = await fetchTelegramStatus();

  return (
    <AlertsDashboard
      rules={rules}
      events={events}
      telegram={telegram}
      error={error}
      actions={{
        createRule: createAlertRuleAction,
        evaluate: evaluateAlertsAction,
        pauseRule: pauseAlertRuleAction,
        archiveRule: archiveAlertRuleAction,
        acknowledgeEvent: acknowledgeAlertEventAction,
        dismissEvent: dismissAlertEventAction,
        markFalsePositive: markFalsePositiveAction,
        sendTelegram: sendTelegramAction,
      }}
    />
  );
}
