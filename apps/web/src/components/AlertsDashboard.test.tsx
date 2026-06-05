import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { AlertEvent, AlertRule, TelegramStatus } from "@/lib/alerts";
import type { RuntimeErrorInfo } from "@/lib/pythonRunner";
import { AlertsDashboard } from "./AlertsDashboard";

const rule: AlertRule = {
  id: "rule-1",
  name: "BBCA threshold review",
  description: "Check local close against a threshold.",
  rule_type: "price_above",
  ticker: "BBCA.JK",
  parameters: { threshold: 9000 },
  is_active: true,
  created_at: "2026-06-05T09:00:00Z",
  updated_at: "2026-06-05T09:00:00Z",
  archived_at: null,
};

const event: AlertEvent = {
  id: "event-1",
  rule_id: "rule-1",
  evaluation_id: "eval-1",
  ticker: "BBCA.JK",
  event_type: "price_above",
  severity: "info",
  title: "Rule condition matched",
  message: "BBCA.JK matched price_above with value 9500 and threshold 9000.",
  status: "new",
  created_at: "2026-06-05T09:01:00Z",
  acknowledged_at: null,
  dismissed_at: null,
  false_positive_at: null,
  resolved_at: null,
  notes: null,
};

const telegram: TelegramStatus = {
  enabled: false,
  configured: false,
  status: "not_configured",
  bot_token_configured: false,
  chat_id_configured: false,
  message: "Telegram delivery is not configured in this V1-S6 slice.",
};

const configuredTelegram: TelegramStatus = {
  enabled: true,
  configured: true,
  status: "configured",
  bot_token_configured: true,
  chat_id_configured: true,
  message: "Telegram delivery is configured.",
};

describe("AlertsDashboard", () => {
  it("renders page header and no-signal copy", () => {
    const html = renderToStaticMarkup(
      <AlertsDashboard rules={[rule]} events={[event]} telegram={telegram} error={null} />,
    );

    expect(html).toContain("Alerts");
    expect(html).toContain("Review local alert rules and matched conditions");
    expect(html).toContain("not trading instructions");
    expect(html).not.toContain("buy");
    expect(html).not.toContain("sell");
    expect(html).not.toContain("buy signal");
    expect(html).not.toContain("profit opportunity");
  });

  it("renders no rules and no events empty states", () => {
    const html = renderToStaticMarkup(
      <AlertsDashboard rules={[]} events={[]} telegram={telegram} error={null} />,
    );

    expect(html).toContain("No alert rules yet");
    expect(html).toContain("Create a local rule");
    expect(html).toContain("No alert events yet");
    expect(html).toContain("Evaluate alerts");
  });

  it("renders migration-required state without raw traceback", () => {
    const error: RuntimeErrorInfo = {
      code: "schema_stale",
      message: "Local alert schema is not ready.",
      details: "Run migration before using alerts.",
      recommended_command: "uv run python -m scripts.migrate",
    };
    const html = renderToStaticMarkup(
      <AlertsDashboard rules={[]} events={[]} telegram={telegram} error={error} />,
    );

    expect(html).toContain("Migration required");
    expect(html).toContain("scripts.migrate");
    expect(html).not.toContain("Traceback");
    expect(html).not.toContain("no such table");
    expect(html).not.toContain("D:/DevSpace");
  });

  it("renders rules, events, and lifecycle actions", () => {
    const html = renderToStaticMarkup(
      <AlertsDashboard rules={[rule]} events={[event]} telegram={telegram} error={null} />,
    );

    expect(html).toContain("BBCA threshold review");
    expect(html).toContain("price above");
    expect(html).toContain("threshold: 9000");
    expect(html).toContain("Pause rule");
    expect(html).toContain("Archive rule");
    expect(html).toContain("Rule condition matched");
    expect(html).toContain("Acknowledge");
    expect(html).toContain("Dismiss");
    expect(html).toContain("Mark false positive");
  });

  it("renders false-positive state and keeps event in history", () => {
    const html = renderToStaticMarkup(
      <AlertsDashboard
        rules={[rule]}
        events={[
          {
            ...event,
            status: "marked_false_positive",
            false_positive_at: "2026-06-05T10:00:00Z",
          },
        ]}
        telegram={telegram}
        error={null}
      />,
    );

    expect(html).toContain("False Positive");
    expect(html).toContain("Marked false positive");
    expect(html).toContain("helps review alert quality later");
  });

  it("renders telegram disabled as a non-error state", () => {
    const html = renderToStaticMarkup(
      <AlertsDashboard rules={[]} events={[]} telegram={telegram} error={null} />,
    );

    expect(html).toContain("Telegram delivery is disabled");
    expect(html).toContain("Local alert events remain available");
    expect(html).not.toContain("Command failed");
  });

  it("renders configured Telegram state and explicit send action without token leak", () => {
    const html = renderToStaticMarkup(
      <AlertsDashboard
        rules={[rule]}
        events={[event]}
        telegram={configuredTelegram}
        error={null}
      />,
    );

    expect(html).toContain("Telegram delivery is optional");
    expect(html).toContain("Configured");
    expect(html).toContain("Send to Telegram");
    expect(html).not.toContain("secret-token");
    expect(html).not.toContain("CHAT_SECRET_SENTINEL");
    expect(html).not.toContain("Traceback");
  });
});
