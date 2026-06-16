import { NextRequest, NextResponse } from "next/server";
import { spawn, execSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync, unlinkSync, openSync } from "node:fs";
import { resolve } from "node:path";
import type { ControlAction, ControlResult } from "@/lib/hermes";

const PID_PATH = resolve(process.cwd(), "..", "..", "data", "private", "hermes.pid");
const LOG_PATH = resolve(process.cwd(), "..", "..", "data", "private", "hermes.log");
const ROOT = resolve(process.cwd(), "..", "..");

function findPython(): string {
  try {
    execSync("uv --version", { stdio: "pipe", windowsHide: true });
    return "uv";
  } catch {
    try {
      execSync("python --version", { stdio: "pipe", windowsHide: true });
      return "python";
    } catch {
      return process.platform === "win32" ? "python" : "python3";
    }
  }
}

async function startHermes(): Promise<ControlResult> {
  if (existsSync(PID_PATH)) {
    const existing = parseInt(readFileSync(PID_PATH, "utf-8").trim(), 10);
    if (!isNaN(existing)) {
      try {
        process.kill(existing, 0);
        return { ok: false, message: `Hermes already running (PID ${existing}).` };
      } catch {
        // PID stale, continue to start
      }
    }
    try { unlinkSync(PID_PATH); } catch { /* ignore */ }
  }

  const python = findPython();
  const args = python === "uv" ? ["run", "python", "-m", "services.hermes"] : ["-m", "services.hermes"];

  const logFile = openSync(LOG_PATH, "a");
  const child = spawn(python, args, {
    cwd: ROOT,
    stdio: ["ignore", logFile, logFile],
    detached: true,
    windowsHide: true,
  });

  child.unref();
  writeFileSync(PID_PATH, String(child.pid ?? ""), "utf-8");
  return { ok: true, message: `Hermes started (PID ${child.pid}).` };
}

async function stopHermes(): Promise<ControlResult> {
  if (!existsSync(PID_PATH)) {
    return { ok: false, message: "Hermes is not running." };
  }

  const pidStr = readFileSync(PID_PATH, "utf-8").trim();
  const pid = parseInt(pidStr, 10);
  if (isNaN(pid)) {
    try { unlinkSync(PID_PATH); } catch { /* ignore */ }
    return { ok: false, message: "Invalid PID file. Removed." };
  }

  try {
    if (process.platform === "win32") {
      execSync(`taskkill /PID ${pid} /F`, { stdio: "pipe", windowsHide: true });
    } else {
      process.kill(pid, "SIGTERM");
    }
    try { unlinkSync(PID_PATH); } catch { /* ignore */ }
    return { ok: true, message: `Hermes stopped (PID ${pid}).` };
  } catch {
    try { unlinkSync(PID_PATH); } catch { /* ignore */ }
    return { ok: true, message: `Hermes process ${pid} already exited.` };
  }
}

export async function POST(req: NextRequest): Promise<NextResponse> {
  let body: { action?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, message: "Invalid JSON body." } satisfies ControlResult, { status: 400 });
  }

  const action = body.action as ControlAction;
  if (action !== "start" && action !== "stop") {
    return NextResponse.json({ ok: false, message: "Action must be 'start' or 'stop'." } satisfies ControlResult, { status: 400 });
  }

  const result = action === "start" ? await startHermes() : await stopHermes();
  return NextResponse.json(result, { status: result.ok ? 200 : 409 });
}
