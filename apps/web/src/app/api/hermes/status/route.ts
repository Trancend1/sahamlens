import { NextResponse } from "next/server";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { HermesConfig, HermesStatus, ProcessState } from "@/lib/hermes";

const PID_PATH = resolve(process.cwd(), "..", "..", "data", "private", "hermes.pid");

function readHermesConfig(): HermesConfig {
  const enabledRaw = process.env.SAHAMLENS_HERMES_ENABLED ?? "";
  const enabled = /^(1|true|yes)$/i.test(enabledRaw.trim());
  const hasTelegramToken = Boolean(process.env.SAHAMLENS_TELEGRAM_BOT_TOKEN);
  const hasTelegramChat = Boolean(process.env.SAHAMLENS_TELEGRAM_CHAT_ID);
  const providerName = process.env.SAHAMLENS_LLM_PROVIDER || "not set";
  const hasLlmKey = Boolean(process.env.SAHAMLENS_LLM_API_KEY);
  const hasAnthropicKey = Boolean(process.env.ANTHROPIC_API_KEY);

  return {
    enabled,
    telegramConfigured: hasTelegramToken && hasTelegramChat,
    providerName,
    providerConfigured: hasLlmKey || hasAnthropicKey,
  };
}

function checkProcessState(): ProcessState {
  if (!existsSync(PID_PATH)) {
    return { running: false, pid: null };
  }
  const raw = readFileSync(PID_PATH, "utf-8").trim();
  const pid = parseInt(raw, 10);
  if (isNaN(pid)) {
    return { running: false, pid: null };
  }
  try {
    process.kill(pid, 0);
    return { running: true, pid };
  } catch {
    return { running: false, pid: null };
  }
}

export async function GET(): Promise<NextResponse> {
  const config = readHermesConfig();
  const process = checkProcessState();
  return NextResponse.json({ config, process } satisfies HermesStatus);
}
