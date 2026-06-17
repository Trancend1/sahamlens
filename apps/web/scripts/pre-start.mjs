#!/usr/bin/env node

import { execSync } from "node:child_process";
import { existsSync, accessSync, constants, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "..", "..", "..");

const green = (s) => `\x1b[32m${s}\x1b[0m`;
const yellow = (s) => `\x1b[33m${s}\x1b[0m`;
const red = (s) => `\x1b[31m${s}\x1b[0m`;
const cyan = (s) => `\x1b[36m${s}\x1b[0m`;
const dim = (s) => `\x1b[2m${s}\x1b[0m`;

const log = (...args) => console.log("[pre-start]", ...args);

function detectPython() {
  if (process.env.PYTHON_BIN) {
    const p = process.env.PYTHON_BIN.replace(/^"|"$/g, "");
    try {
      execSync(`"${p}" --version`, { stdio: "pipe", windowsHide: true });
      return { cmd: `"${p}"`, label: p };
    } catch {
      log(yellow(`PYTHON_BIN set to "${p}" but not working, falling back...`));
    }
  }
  try {
    execSync("uv --version", { stdio: "pipe", windowsHide: true });
    try {
      const out = execSync('uv run python -c "import sys; print(sys.executable)"', {
        stdio: "pipe", encoding: "utf8", timeout: 15000, windowsHide: true,
      });
      const resolved = out.toString().trim();
      return { cmd: "uv run python", label: resolved };
    } catch {
      return { cmd: "uv run python", label: "uv run python" };
    }
  } catch {
    // uv not found
  }
  try {
    execSync("python --version", { stdio: "pipe", windowsHide: true });
    return { cmd: "python", label: "python" };
  } catch {
    // python not found
  }
  if (process.platform !== "win32") {
    try {
      execSync("python3 --version", { stdio: "pipe", windowsHide: true });
      return { cmd: "python3", label: "python3" };
    } catch {
      // python3 not found
    }
  }
  return null;
}

function printStatus(label, ok, detail = "") {
  const icon = ok ? green("\u2713") : red("\u2717");
  log(`${icon} ${label}${detail ? dim(` \u2014 ${detail}`) : ""}`);
}

function main() {
  const header = `${cyan("\u2550".repeat(46))}\n${cyan("\u2551")}  SahamLens \u2014 Pre-Start Setup${" ".repeat(25)}${cyan("\u2551")}\n${cyan("\u2550".repeat(46))}`;
  console.log(`\n${header}\n`);

  const errors = [];

  // --- 1. Python ---
  const py = detectPython();
  if (!py) {
    printStatus("Python", false, "Not found. Install Python 3.11+ from https://python.org");
    errors.push("Python not found. Install Python 3.11+.");
  } else {
    printStatus("Python", true, py.label);
  }

  // --- 2. .env.local ---
  const envPath = resolve(REPO_ROOT, ".env.local");
  if (!existsSync(envPath)) {
    printStatus(".env.local", false, "Missing. AI features will not work until configured.");
    log(yellow("  \u2192 Copy .env.example to .env.local and configure LLM keys"));
  } else {
    printStatus(".env.local", true);
  }

  // --- 3. data/private/ writable ---
  const dbDir = resolve(REPO_ROOT, "data", "private");
  try {
    mkdirSync(dbDir, { recursive: true });
    accessSync(dbDir, constants.W_OK);
    printStatus("data/private/", true, dbDir);
  } catch {
    printStatus("data/private/", false, "Not writable");
    errors.push(`Directory ${dbDir} is not writable`);
  }

  // --- 4. Config files ---
  const cfgDir = resolve(REPO_ROOT, "config");
  const hasBudget = existsSync(resolve(cfgDir, "cost_budget.yml"));
  const hasExample = existsSync(resolve(cfgDir, "cost_budget.example.yml"));
  if (hasBudget) {
    printStatus("config/cost_budget.yml", true);
  } else if (hasExample) {
    printStatus("config/cost_budget.yml", false, "Using .example fallback");
  } else {
    printStatus("config/cost_budget.yml", false, "Missing, no fallback");
  }

  // --- Block on critical failures ---
  if (errors.length > 0) {
    console.error(`\n${red("\u2717 Pre-start checks failed:")}`);
    for (const e of errors) console.error(`  ${red("\u2022")} ${e}`);
    console.error(`\n${red("Dev server will not start. Fix the issues above and retry.\n")}`);
    process.exit(1);
  }

  // --- 5. Run migration ---
  log(cyan("Running database migration..."));
  try {
    const out = execSync(`${py.cmd} -m scripts.migrate`, {
      cwd: REPO_ROOT, encoding: "utf8", timeout: 60000, windowsHide: true,
    });
    const lines = out.trim().split("\n").filter(Boolean);
    for (const line of lines) printStatus("migrate", true, line);
  } catch (err) {
    const msg = err.stderr?.toString().trim() || err.message;
    printStatus("migrate", false, msg);
    log(red("Migration failed. Dev server will not start."));
    process.exit(1);
  }

  // --- 6. Run bootstrap ---
  log(cyan("Running runtime bootstrap..."));
  try {
    const out = execSync(`${py.cmd} -m scripts.runtime bootstrap --json`, {
      cwd: REPO_ROOT, encoding: "utf8", timeout: 120000, windowsHide: true,
    });
    const result = JSON.parse(out.trim());
    for (const step of result.steps || []) {
      const ok = step.status === "completed" || step.status === "skipped";
      printStatus(`bootstrap:${step.name}`, ok, step.message);
    }
    if (result.ok) {
      log(green("Bootstrap completed successfully."));
    } else {
      log(yellow("Bootstrap completed with warnings."));
    }
  } catch (err) {
    log(yellow(`Bootstrap warning (non-fatal): ${err.message}`));
  }

  console.log(`\n${green("\u2713 Pre-start setup complete. Starting dev server...")}\n`);
}

main();
