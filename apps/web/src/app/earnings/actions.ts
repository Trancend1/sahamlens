"use server";

import { revalidatePath } from "next/cache";
import {
  archiveEarningsEvent,
  createEarningsEvent,
  generateEarningsSummary,
  updateEarningsEventNotes,
  type EarningsSourceType,
} from "@/lib/earnings";

const EARNINGS_PATH = "/earnings";

export async function createEarningsEventAction(formData: FormData): Promise<void> {
  await createEarningsEvent({
    ticker: requiredString(formData, "ticker"),
    period: requiredString(formData, "period"),
    eventDate: requiredString(formData, "eventDate"),
    sourceType: requiredString(formData, "sourceType") as EarningsSourceType,
    sourceRef: optionalString(formData, "sourceRef"),
    notes: optionalString(formData, "notes"),
  });
  revalidatePath(EARNINGS_PATH);
}

export async function generateEarningsSummaryAction(formData: FormData): Promise<void> {
  await generateEarningsSummary(requiredString(formData, "eventId"));
  revalidatePath(EARNINGS_PATH);
}

export async function updateEarningsNotesAction(formData: FormData): Promise<void> {
  await updateEarningsEventNotes(
    requiredString(formData, "eventId"),
    requiredString(formData, "notes"),
  );
  revalidatePath(EARNINGS_PATH);
}

export async function archiveEarningsEventAction(formData: FormData): Promise<void> {
  await archiveEarningsEvent(requiredString(formData, "eventId"));
  revalidatePath(EARNINGS_PATH);
}

function requiredString(formData: FormData, key: string): string {
  const value = formData.get(key);
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${key} is required`);
  }
  return value.trim();
}

function optionalString(formData: FormData, key: string): string | undefined {
  const value = formData.get(key);
  if (typeof value !== "string" || !value.trim()) return undefined;
  return value.trim();
}
