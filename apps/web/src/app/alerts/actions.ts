"use server";

import { revalidatePath } from "next/cache";
import {
  acknowledgeAlertEvent,
  archiveAlertRule,
  createAlertRule,
  dismissAlertEvent,
  evaluateAlerts,
  markAlertEventFalsePositive,
  pauseAlertRule,
  sendAlertEventToTelegram,
  type AlertRuleType,
} from "@/lib/alerts";

const ALERTS_PATH = "/alerts";

export async function createAlertRuleAction(formData: FormData): Promise<void> {
  const name = requiredString(formData, "name");
  const ticker = requiredString(formData, "ticker");
  const threshold = Number(requiredString(formData, "threshold"));
  const ruleType = requiredString(formData, "ruleType") as AlertRuleType;
  await createAlertRule({
    name,
    ticker,
    threshold,
    ruleType,
    description: `${name} local threshold review.`,
  });
  revalidatePath(ALERTS_PATH);
}

export async function evaluateAlertsAction(): Promise<void> {
  await evaluateAlerts();
  revalidatePath(ALERTS_PATH);
}

export async function pauseAlertRuleAction(formData: FormData): Promise<void> {
  await pauseAlertRule(requiredString(formData, "ruleId"));
  revalidatePath(ALERTS_PATH);
}

export async function archiveAlertRuleAction(formData: FormData): Promise<void> {
  await archiveAlertRule(requiredString(formData, "ruleId"));
  revalidatePath(ALERTS_PATH);
}

export async function acknowledgeAlertEventAction(formData: FormData): Promise<void> {
  await acknowledgeAlertEvent(requiredString(formData, "eventId"));
  revalidatePath(ALERTS_PATH);
}

export async function dismissAlertEventAction(formData: FormData): Promise<void> {
  await dismissAlertEvent(requiredString(formData, "eventId"));
  revalidatePath(ALERTS_PATH);
}

export async function markFalsePositiveAction(formData: FormData): Promise<void> {
  await markAlertEventFalsePositive(requiredString(formData, "eventId"));
  revalidatePath(ALERTS_PATH);
}

export async function sendTelegramAction(formData: FormData): Promise<void> {
  await sendAlertEventToTelegram(requiredString(formData, "eventId"));
  revalidatePath(ALERTS_PATH);
}

function requiredString(formData: FormData, key: string): string {
  const value = formData.get(key);
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${key} is required`);
  }
  return value.trim();
}
