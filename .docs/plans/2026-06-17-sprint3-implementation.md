# Sprint 3: Operations Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `/operations/*` pages so user can monitor health, run data operations, and edit config without terminal.

**Architecture:** Next.js App Router pages under `/operations/` with shared layout + tab navigation. Data from `GET /api/health` (single source of truth), `GET /api/data/freshness` (existing), and `POST /api/operations/{type}/run` (new unified route). Config read/write `.env.local` directly via Node.js `fs`.

**Tech Stack:** Next.js 15 App Router, TypeScript strict, Tailwind CSS. Config read/write via Node.js `fs`.

---

### Task 1: Operations Registry

**Files:**
- Create: `apps/web/src/lib/operations.ts`
- Test: `apps/web/src/lib/operations.test.ts`

**Depends on:** Nothing

- [ ] **Step 1: Write the test**

```ts
// apps/web/src/lib/operations.test.ts
import { describe, it, expect } from "vitest";
import { OPERATIONS, getOperation, getOperationsByCategory } from "./operations";

describe("operations registry", () => {
  it("should have all expected operations", () => {
    const ids = OPERATIONS.map((o) => o.id);
    expect(ids).toContain("provider_health");
    expect(ids).toContain("prices");
    expect(ids).toContain("fundamentals");
    expect(ids).toContain("news");
    expect(ids).toContain("alerts");
    expect(ids).toContain("screener");
    expect(ids).toContain("strategy_rules");
    expect(ids).toContain("weekly_review");
  });

  it("each operation should have required fields", () => {
    for (const op of OPERATIONS) {
      expect(op.id).toBeTruthy();
      expect(op.name).toBeTruthy();
      expect(op.category).toBeTruthy();
      expect(op.route).toMatch(/^\/api\//);
      expect(op.freshnessKey).toBeTruthy();
      expect(op.timeoutMs).toBeGreaterThan(0);
    }
  });

  it("should retrieve operation by id", () => {
    const op = getOperation("prices");
    expect(op?.id).toBe("prices");
    expect(op?.name).toBe("Refresh Prices");
  });

  it("should return undefined for unknown id", () => {
    expect(getOperation("nonexistent")).toBeUndefined();
  });

  it("should group operations by category", () => {
    const byCat = getOperationsByCategory();
    expect(byCat.provider).toBeDefined();
    expect(byCat.provider.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/lib/operations.test.ts --reporter=verbose`
Expected: FAIL — module not found

- [ ] **Step 3: Write the registry**

```ts
// apps/web/src/lib/operations.ts
export type OperationCategory = "provider" | "analysis" | "review";

export interface Operation {
  id: string;
  name: string;
  description: string;
  category: OperationCategory;
  route: string;
  freshnessKey: string;
  timeoutMs: number;
}

export const OPERATIONS: Operation[] = [
  {
    id: "provider_health",
    name: "Provider Health",
    description: "Check data provider connectivity and freshness",
    category: "provider",
    route: "/api/operations/provider_health/run",
    freshnessKey: "provider_health",
    timeoutMs: 120_000,
  },
  {
    id: "prices",
    name: "Prices",
    description: "Ingest historical price data from watchlist",
    category: "provider",
    route: "/api/operations/prices/run",
    freshnessKey: "prices",
    timeoutMs: 180_000,
  },
  {
    id: "fundamentals",
    name: "Fundamentals",
    description: "Refresh fundamental snapshots from watchlist",
    category: "provider",
    route: "/api/operations/fundamentals/run",
    freshnessKey: "fundamentals",
    timeoutMs: 180_000,
  },
  {
    id: "news",
    name: "News",
    description: "Fetch and summarize news from RSS feeds",
    category: "provider",
    route: "/api/operations/news/run",
    freshnessKey: "news",
    timeoutMs: 180_000,
  },
  {
    id: "alerts",
    name: "Alerts",
    description: "Evaluate alert rules against current data",
    category: "analysis",
    route: "/api/operations/alerts/run",
    freshnessKey: "alerts",
    timeoutMs: 60_000,
  },
  {
    id: "screener",
    name: "Screener",
    description: "Run screening rules on watchlist",
    category: "analysis",
    route: "/api/operations/screener/run",
    freshnessKey: "screener",
    timeoutMs: 120_000,
  },
  {
    id: "strategy_rules",
    name: "Strategy Rules",
    description: "Evaluate strategy rule discipline checks",
    category: "review",
    route: "/api/operations/strategy_rules/run",
    freshnessKey: "strategy_rules",
    timeoutMs: 60_000,
  },
  {
    id: "weekly_review",
    name: "Weekly Review",
    description: "Generate weekly journal consistency review",
    category: "review",
    route: "/api/operations/weekly_review/run",
    freshnessKey: "weekly_review",
    timeoutMs: 120_000,
  },
];

export function getOperation(id: string): Operation | undefined {
  return OPERATIONS.find((op) => op.id === id);
}

export function getOperationsByCategory(): Record<OperationCategory, Operation[]> {
  const result: Record<OperationCategory, Operation[]> = {
    provider: [],
    analysis: [],
    review: [],
  };
  for (const op of OPERATIONS) {
    result[op.category].push(op);
  }
  return result;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/lib/operations.test.ts --reporter=verbose`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/lib/operations.ts apps/web/src/lib/operations.test.ts
git commit -m "feat(s3): add operations registry lib"
```

---

### Task 2: Health API + Types

**Files:**
- Create: `apps/web/src/lib/health.ts`
- Create: `apps/web/src/app/api/health/route.ts`
- Test: `apps/web/src/api/health/route.test.ts`

**Depends on:** Nothing (uses existing `runPython`)

- [ ] **Step 1: Write health types**

```ts
// apps/web/src/lib/health.ts
export type OverallStatus = "healthy" | "degraded" | "unhealthy";

export interface ComponentCheck {
  status: "ok" | "degraded" | "fail";
  label: string;
  detail: string;
}

export interface HealthReport {
  overall: OverallStatus;
  summary: string;
  checks: {
    python: ComponentCheck;
    database: ComponentCheck;
    runtime: ComponentCheck;
    llm: ComponentCheck;
  };
  refresh_mode: "manual";
}
```

- [ ] **Step 2: Write the API route test**

```ts
// apps/web/src/app/api/health/route.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GET } from "./route";

vi.mock("@/lib/pythonRunner", () => ({
  runPython: vi.fn(),
  PythonRunnerError: class extends Error {
    constructor(m: string, public stdout = "", public stderr = "", public exitCode: number | null = null) {
      super(m);
      this.name = "PythonRunnerError";
    }
  },
}));

import { runPython } from "@/lib/pythonRunner";

describe("GET /api/health", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return healthy when all checks pass", async () => {
    vi.mocked(runPython).mockResolvedValue({
      data: {
        ok: true,
        status: "ready",
        db_path: "data/private/sahamlens.duckdb",
        python_executable: "python3.12",
        schema_status: "ready",
        applied_migrations: ["001_init"],
        pending_migrations: [],
        missing_tables: [],
        warnings: [],
        errors: [],
        recommended_commands: [],
      },
      rawStdout: "",
      rawStderr: "",
    });

    const res = await GET();
    const body = await res.json();
    expect(body.overall).toBe("healthy");
    expect(body.checks.database.status).toBe("ok");
    expect(body.checks.runtime.status).toBe("ok");
    expect(body.checks.python.status).toBe("ok");
  });

  it("should return degraded when LLM is not configured", async () => {
    vi.mocked(runPython).mockResolvedValue({
      data: {
        ok: true,
        status: "ready",
        db_path: "data/private/sahamlens.duckdb",
        python_executable: "python3.12",
        schema_status: "ready",
        applied_migrations: ["001_init"],
        pending_migrations: [],
        missing_tables: [],
        warnings: [{ code: "llm", message: "No LLM provider configured", recommended_command: null }],
        errors: [],
        recommended_commands: [],
      },
      rawStdout: "",
      rawStderr: "",
    });

    const res = await GET();
    const body = await res.json();
    expect(body.overall).toBe("degraded");
    expect(body.checks.llm.status).toBe("degraded");
  });

  it("should return unhealthy when runtime fails", async () => {
    vi.mocked(runPython).mockRejectedValue(new Error("Python not found"));

    const res = await GET();
    const body = await res.json();
    expect(body.overall).toBe("unhealthy");
    expect(body.checks.runtime.status).toBe("fail");
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/app/api/health/route.test.ts --reporter=verbose`
Expected: FAIL — module not found

- [ ] **Step 4: Write the API route**

```ts
// apps/web/src/app/api/health/route.ts
import { NextResponse } from "next/server";
import { runPython } from "@/lib/pythonRunner";
import type { RuntimeStatus } from "@/lib/runtime";
import type { OverallStatus, ComponentCheck, HealthReport } from "@/lib/health";

function makeCheck(
  status: "ok" | "degraded" | "fail",
  label: string,
  detail: string
): ComponentCheck {
  return { status, label, detail };
}

async function checkRuntime(): Promise<{
  runtime: ComponentCheck;
  python: ComponentCheck;
  database: ComponentCheck;
}> {
  try {
    const { data } = await runPython<RuntimeStatus>("scripts.runtime", {
      args: ["status", "--json"],
      timeoutMs: 30_000,
    });
    const schemaReady = data.schema_status === "ready";
    return {
      runtime: makeCheck(
        schemaReady ? "ok" : "degraded",
        "Runtime",
        schemaReady ? "Schema ready" : `Schema: ${data.schema_status}`
      ),
      python: makeCheck(
        data.python_executable ? "ok" : "degraded",
        "Core Engine",
        data.python_executable ?? "Not resolved"
      ),
      database: makeCheck(
        data.db_path ? "ok" : "fail",
        "Database",
        data.db_path ? `Connected (${data.applied_migrations.length} migrations)` : "Not configured"
      ),
    };
  } catch {
    return {
      runtime: makeCheck("fail", "Runtime", "Could not query runtime status"),
      python: makeCheck("fail", "Core Engine", "Python subprocess failed"),
      database: makeCheck("fail", "Database", "Could not connect to DuckDB"),
    };
  }
}

async function checkLlm(): Promise<ComponentCheck> {
  try {
    const { data } = await runPython<{
      ok: boolean;
      provider: string;
      model: string;
      configured: boolean;
      error?: string;
    }>("scripts.llm_status", {
      args: ["--json"],
      timeoutMs: 15_000,
    });
    if (data.configured) {
      return makeCheck("ok", "LLM Provider", `${data.provider} / ${data.model}`);
    }
    return makeCheck("degraded", "LLM Provider", data.error ?? "Not configured");
  } catch {
    return makeCheck("degraded", "LLM Provider", "Could not verify LLM status");
  }
}

function computeOverall(checks: HealthReport["checks"]): {
  overall: OverallStatus;
  summary: string;
} {
  const statuses = Object.values(checks).map((c) => c.status);
  if (statuses.some((s) => s === "fail")) {
    return { overall: "unhealthy", summary: "Core services unavailable." };
  }
  if (statuses.some((s) => s === "degraded")) {
    return { overall: "degraded", summary: "Some non-critical services unavailable." };
  }
  return { overall: "healthy", summary: "All required services available." };
}

export async function GET(): Promise<NextResponse> {
  const [runtimeChecks, llmCheck] = await Promise.all([
    checkRuntime(),
    checkLlm(),
  ]);

  const checks: HealthReport["checks"] = {
    python: runtimeChecks.python,
    database: runtimeChecks.database,
    runtime: runtimeChecks.runtime,
    llm: llmCheck,
  };

  const { overall, summary } = computeOverall(checks);

  return NextResponse.json({
    overall,
    summary,
    checks,
    refresh_mode: "manual",
  } satisfies HealthReport);
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/app/api/health/route.test.ts --reporter=verbose`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/lib/health.ts apps/web/src/app/api/health/route.ts apps/web/src/app/api/health/route.test.ts
git commit -m "feat(s3): add /api/health endpoint as single source of truth"
```

---

### Task 3: Config API

**Files:**
- Create: `apps/web/src/app/api/config/route.ts`
- Test: `apps/web/src/app/api/config/route.test.ts`

**Depends on:** Nothing (uses Node.js `fs` directly)

- [ ] **Step 1: Write the test**

```ts
// apps/web/src/app/api/config/route.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GET, POST } from "./route";

vi.mock("node:fs", () => ({
  existsSync: vi.fn(),
  readFileSync: vi.fn(),
  writeFileSync: vi.fn(),
  readdirSync: vi.fn(),
  statSync: vi.fn(),
}));

import fs from "node:fs";

const mockEnv = `
SAHAMLENS_LLM_PROVIDER=openrouter
SAHAMLENS_LLM_BASE_URL=https://openrouter.ai/api/v1
SAHAMLENS_LLM_MODEL=anthropic/claude-sonnet-4-6
DUCKDB_PATH=./data/private/sahamlens.duckdb
`;

describe("GET /api/config", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fs.existsSync).mockReturnValue(true);
    vi.mocked(fs.readFileSync).mockReturnValue(mockEnv);
  });

  it("should return LLM config section", async () => {
    const req = new Request("http://localhost/api/config?section=llm");
    const res = await GET(req);
    const body = await res.json();
    expect(body.section).toBe("llm");
    expect(body.config.provider).toBe("openrouter");
    expect(body.config.baseUrl).toBe("https://openrouter.ai/api/v1");
    expect(body.config.model).toBe("anthropic/claude-sonnet-4-6");
    expect(body.config.apiKey).toBeUndefined();
  });

  it("should return app config section", async () => {
    const req = new Request("http://localhost/api/config?section=app");
    const res = await GET(req);
    const body = await res.json();
    expect(body.section).toBe("app");
    expect(body.config.dataDir).toBe("./data/private/sahamlens.duckdb");
  });

  it("should return 400 for unknown section", async () => {
    const req = new Request("http://localhost/api/config?section=unknown");
    const res = await GET(req);
    expect(res.status).toBe(400);
  });
});

describe("POST /api/config", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fs.existsSync).mockReturnValue(true);
    vi.mocked(fs.readFileSync).mockReturnValue(mockEnv);
  });

  it("should update LLM config", async () => {
    const req = new Request("http://localhost/api/config?section=llm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: "anthropic",
        model: "claude-sonnet-4-20250514",
        baseUrl: "",
        apiKey: "sk-ant-new-key",  # pragma: allowlist secret
      }),
    });
    const res = await POST(req);
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(fs.writeFileSync).toHaveBeenCalled();
  });

  it("should return 400 for missing section", async () => {
    const req = new Request("http://localhost/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/app/api/config/route.test.ts --reporter=verbose`
Expected: FAIL

- [ ] **Step 3: Write the API route**

```ts
// apps/web/src/app/api/config/route.ts
import { NextRequest, NextResponse } from "next/server";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const ENV_PATH = resolve(process.cwd(), "..", "..", ".env.local");

function readEnvFile(): Record<string, string> {
  if (!existsSync(ENV_PATH)) return {};
  const raw = readFileSync(ENV_PATH, "utf-8");
  const vars: Record<string, string> = {};
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eqIdx = trimmed.indexOf("=");
    if (eqIdx === -1) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    const val = trimmed.slice(eqIdx + 1).trim();
    if (key) vars[key] = val;
  }
  return vars;
}

function writeEnvFile(vars: Record<string, string>): void {
  const lines: string[] = [];
  lines.push("# SahamLens environment — generated by Config UI");
  lines.push("# WARNING: local changes may be overwritten by Config UI");
  lines.push("");
  const keys = Object.keys(vars).sort();
  for (const key of keys) {
    lines.push(`${key}=${vars[key] ?? ""}`);
  }
  writeFileSync(ENV_PATH, lines.join("\n") + "\n", "utf-8");
}

const LLM_KEYS = [
  "SAHAMLENS_LLM_PROVIDER",
  "SAHAMLENS_LLM_BASE_URL",
  "SAHAMLENS_LLM_API_KEY",
  "SAHAMLENS_LLM_MODEL",
  "ANTHROPIC_API_KEY",
] as const;

export async function GET(req: NextRequest): Promise<NextResponse> {
  const section = req.nextUrl.searchParams.get("section");

  if (!section || !["llm", "app"].includes(section)) {
    return NextResponse.json({ error: "Unknown section. Use ?section=llm|app" }, { status: 400 });
  }

  const env = readEnvFile();

  if (section === "llm") {
    return NextResponse.json({
      section: "llm",
      config: {
        provider: env.SAHAMLENS_LLM_PROVIDER ?? "",
        baseUrl: env.SAHAMLENS_LLM_BASE_URL ?? "",
        model: env.SAHAMLENS_LLM_MODEL ?? "",
      },
    });
  }

  return NextResponse.json({
    section: "app",
    config: {
      dataDir: env.DUCKDB_PATH ?? "./data/private/sahamlens.duckdb",
    },
  });
}

export async function POST(req: NextRequest): Promise<NextResponse> {
  const section = req.nextUrl.searchParams.get("section");

  if (!section || !["llm", "app"].includes(section)) {
    return NextResponse.json({ error: "Unknown section. Use ?section=llm|app" }, { status: 400 });
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const env = readEnvFile();

  if (section === "llm") {
    if (body.provider !== undefined) env.SAHAMLENS_LLM_PROVIDER = String(body.provider);
    if (body.baseUrl !== undefined) env.SAHAMLENS_LLM_BASE_URL = String(body.baseUrl);
    if (body.model !== undefined) env.SAHAMLENS_LLM_MODEL = String(body.model);
    if (body.apiKey !== undefined) env.SAHAMLENS_LLM_API_KEY = String(body.apiKey);
    if (body.anthropicKey !== undefined) env.ANTHROPIC_API_KEY = String(body.anthropicKey);
  }

  writeEnvFile(env);
  return NextResponse.json({ ok: true, section });
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/app/api/config/route.test.ts --reporter=verbose`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/app/api/config/route.ts apps/web/src/app/api/config/route.test.ts
git commit -m "feat(s3): add /api/config endpoint for LLM + app config"
```

---

### Task 4: Unified Run API Route

**Files:**
- Create: `apps/web/src/app/api/operations/[type]/run/route.ts`
- Test: `apps/web/src/app/api/operations/[type]/run/route.test.ts`

**Depends on:** Task 1 (operations registry)

- [ ] **Step 1: Write the test**

```ts
// apps/web/src/app/api/operations/[type]/run/route.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { POST } from "./route";

vi.mock("@/lib/pythonRunner", () => ({
  runPython: vi.fn(),
  PythonRunnerError: class extends Error {
    constructor(m: string, public stdout = "", public stderr = "", public exitCode: number | null = null) {
      super(m);
      this.name = "PythonRunnerError";
    }
  },
}));

import { runPython } from "@/lib/pythonRunner";

describe("POST /api/operations/[type]/run", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should run provider_health operation", async () => {
    vi.mocked(runPython).mockResolvedValue({
      data: { ok: true },
      rawStdout: "",
      rawStderr: "",
    });

    const req = new Request("http://localhost/api/operations/provider_health/run", { method: "POST" });
    const res = await POST(req, { params: Promise.resolve({ type: "provider_health" }) });
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(runPython).toHaveBeenCalledWith("scripts.provider_health", expect.any(Object));
  });

  it("should run prices operation", async () => {
    vi.mocked(runPython).mockResolvedValue({
      data: { ok: true },
      rawStdout: "",
      rawStderr: "",
    });

    const req = new Request("http://localhost/api/operations/prices/run", { method: "POST" });
    const res = await POST(req, { params: Promise.resolve({ type: "prices" }) });
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(runPython).toHaveBeenCalledWith("scripts.ingest_prices", expect.any(Object));
  });

  it("should return 400 for unknown operation type", async () => {
    const req = new Request("http://localhost/api/operations/unknown/run", { method: "POST" });
    const res = await POST(req, { params: Promise.resolve({ type: "unknown" }) });
    expect(res.status).toBe(400);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/app/api/operations/[type]/run/route.test.ts --reporter=verbose`
Expected: FAIL

- [ ] **Step 3: Write the route**

```ts
// apps/web/src/app/api/operations/[type]/run/route.ts
import { NextRequest, NextResponse } from "next/server";
import { runPython, PythonRunnerError } from "@/lib/pythonRunner";
import { getOperation } from "@/lib/operations";

interface ScriptMapping {
  module: string;
  args: string[];
}

const SCRIPT_MAP: Record<string, ScriptMapping> = {
  provider_health: { module: "scripts.provider_health", args: ["refresh", "--json"] },
  prices: { module: "scripts.ingest_prices", args: ["--from-watchlist", "--days", "7", "--json"] },
  fundamentals: { module: "scripts.fundamentals", args: ["coverage", "refresh", "--from-watchlist", "--json"] },
  news: { module: "scripts.ingest_news", args: ["--from-watchlist", "--json"] },
  alerts: { module: "scripts.alerts", args: ["evaluate", "--json"] },
  screener: { module: "scripts.screener", args: ["run", "--builtin", "fundamentals-basic", "--from-watchlist", "--json"] },
  strategy_rules: { module: "scripts.journal_review", args: ["rules", "evaluate", "--json"] },
  weekly_review: { module: "scripts.journal_review", args: ["review", "generate", "--json"] },
};

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ type: string }> }
): Promise<NextResponse> {
  const { type } = await params;

  if (!getOperation(type)) {
    return NextResponse.json({ ok: false, error: `Unknown operation: ${type}` }, { status: 400 });
  }

  const mapping = SCRIPT_MAP[type];
  if (!mapping) {
    return NextResponse.json({ ok: false, error: `No script mapping for: ${type}` }, { status: 500 });
  }

  try {
    const { data } = await runPython<{ ok: boolean }>(mapping.module, {
      args: mapping.args,
      timeoutMs: getOperation(type)?.timeoutMs ?? 120_000,
    });
    return NextResponse.json({ ok: data.ok ?? true, type });
  } catch (err) {
    const msg = err instanceof PythonRunnerError ? err.stderr || err.message : String(err);
    return NextResponse.json({ ok: false, error: msg, type }, { status: 500 });
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/app/api/operations/[type]/run/route.test.ts --reporter=verbose`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/app/api/operations/\[type\]/run/route.ts apps/web/src/app/api/operations/\[type\]/run/route.test.ts
git commit -m "feat(s3): add unified POST /api/operations/{type}/run route"
```

---

### Task 5: Operations Layout

**Files:**
- Create: `apps/web/src/app/operations/layout.tsx`
- Create: `apps/web/src/app/operations/page.tsx`

**Depends on:** Nothing (pure UI)

- [ ] **Step 1: Create layout with tabs**

```tsx
// apps/web/src/app/operations/layout.tsx
import type { ReactNode } from "react";
import Link from "next/link";

const TABS = [
  { href: "/operations/providers", label: "Providers" },
  { href: "/operations/health", label: "Health" },
  { href: "/operations/config", label: "Config" },
];

export default function OperationsLayout({ children }: { children: ReactNode }) {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 px-6 py-10">
      <header>
        <p className="text-sm uppercase tracking-widest text-muted">SahamLens / Operations</p>
        <h1 className="mt-1 text-3xl font-semibold">Operations</h1>
      </header>

      <nav className="flex gap-1 border-b border-muted/20">
        {TABS.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            className="rounded-t px-4 py-2 text-sm font-medium text-muted transition-colors hover:text-fg aria-[current=page]:border-b-2 aria-[current=page]:border-accent aria-[current=page]:text-accent"
          >
            {tab.label}
          </Link>
        ))}
      </nav>

      {children}
    </main>
  );
}
```

- [ ] **Step 2: Create redirect page**

```tsx
// apps/web/src/app/operations/page.tsx
import { redirect } from "next/navigation";

export default function OperationsPage() {
  redirect("/operations/providers");
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/app/operations/layout.tsx apps/web/src/app/operations/page.tsx
git commit -m "feat(s3): add /operations layout with tab navigation"
```

---

### Task 6: OperationsTable Component + Providers Page

**Files:**
- Create: `apps/web/src/components/OperationsTable.tsx`
- Create: `apps/web/src/app/operations/providers/page.tsx`
- Test: `apps/web/src/components/OperationsTable.test.tsx`

**Depends on:** Task 1 (operations registry), Task 5 (layout)

- [ ] **Step 1: Write the component test**

```tsx
// apps/web/src/components/OperationsTable.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { OperationsTable } from "./OperationsTable";

vi.mock("@/lib/operations", () => ({
  OPERATIONS: [
    { id: "provider_health", name: "Provider Health", description: "Test", category: "provider", route: "/api/test", freshnessKey: "provider_health", timeoutMs: 1000 },
    { id: "alerts", name: "Alerts", description: "Test", category: "analysis", route: "/api/test", freshnessKey: "alerts", timeoutMs: 1000 },
  ],
  getOperationsByCategory: () => ({
    provider: [{ id: "provider_health", name: "Provider Health", description: "Test", category: "provider" as const, route: "/api/test", freshnessKey: "provider_health", timeoutMs: 1000 }],
    analysis: [{ id: "alerts", name: "Alerts", description: "Test", category: "analysis" as const, route: "/api/test", freshnessKey: "alerts", timeoutMs: 1000 }],
    review: [],
  }),
}));

const MOCK_REPORT = {
  has_stale: true,
  stale_count: 1,
  fresh_count: 1,
  total_count: 2,
  stale_types: ["alerts"],
  records: [
    { data_type: "provider_health", status: "fresh", last_refreshed_at: new Date().toISOString(), age_seconds: 100, threshold_seconds: 3600 },
    { data_type: "alerts", status: "stale", last_refreshed_at: new Date(Date.now() - 7200000).toISOString(), age_seconds: 7200, threshold_seconds: 3600 },
  ],
};

describe("OperationsTable", () => {
  it("should render all operations grouped by category", () => {
    render(<OperationsTable report={MOCK_REPORT} />);
    expect(screen.getByText("Provider Health")).toBeDefined();
    expect(screen.getByText("Alerts")).toBeDefined();
  });

  it("should show Run Now buttons", () => {
    render(<OperationsTable report={MOCK_REPORT} />);
    const buttons = screen.getAllByRole("button", { name: /run/i });
    expect(buttons.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/OperationsTable.test.tsx --reporter=verbose`
Expected: FAIL

- [ ] **Step 3: Write the OperationsTable component**

```tsx
// apps/web/src/components/OperationsTable.tsx
"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import { OPERATIONS, getOperationsByCategory } from "@/lib/operations";
import type { OperationCategory } from "@/lib/operations";
import type { FreshnessReport, FreshnessRecord } from "@/lib/runtime";
import { FreshnessBadge } from "@/components/FreshnessBadge";

interface Props {
  report: FreshnessReport;
}

function getRecord(report: FreshnessReport, key: string): FreshnessRecord | undefined {
  return report.records.find((r) => r.data_type === key);
}

function CategorySection({
  category,
  label,
  report,
}: {
  category: OperationCategory;
  label: string;
  report: FreshnessReport;
}) {
  const ops = getOperationsByCategory()[category];
  if (ops.length === 0) return null;

  return (
    <section>
      <h2 className="mb-3 text-xs uppercase tracking-widest text-muted">{label}</h2>
      <div className="grid gap-2">
        {ops.map((op) => {
          const record = getRecord(report, op.freshnessKey);
          return (
            <OperationRow
              key={op.id}
              operation={op}
              record={record}
            />
          );
        })}
      </div>
    </section>
  );
}

function OperationRow({
  operation,
  record,
}: {
  operation: (typeof OPERATIONS)[number];
  record: FreshnessRecord | undefined;
}) {
  const [running, setRunning] = useState(false);

  const handleRun = useCallback(async () => {
    setRunning(true);
    try {
      const res = await fetch(operation.route, { method: "POST" });
      const data = await res.json();
      if (res.ok && data.ok) {
        toast.success(`${operation.name} selesai`);
        window.location.reload();
      } else {
        toast.error(data.error ?? `${operation.name} gagal`);
      }
    } catch {
      toast.error(`Gagal menjalankan ${operation.name}`);
    } finally {
      setRunning(false);
    }
  }, [operation]);

  return (
    <div className="flex items-center justify-between rounded-md border border-muted/30 bg-white/[0.02] px-4 py-3">
      <div className="flex items-center gap-3">
        <div>
          <p className="text-sm font-medium">{operation.name}</p>
          <p className="text-xs text-muted">{operation.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {record?.last_refreshed_at ? (
          <FreshnessBadge iso={record.last_refreshed_at} />
        ) : (
          <span className="rounded border border-muted/40 px-2 py-0.5 text-[10px] uppercase tracking-widest text-muted">
            Never
          </span>
        )}
        <button
          type="button"
          onClick={handleRun}
          disabled={running}
          className="rounded border border-accent/40 px-2.5 py-1 text-xs font-medium text-accent transition-colors hover:bg-accent/10 disabled:opacity-50"
        >
          {running ? "Running..." : "Run Now"}
        </button>
      </div>
    </div>
  );
}

export function OperationsTable({ report }: Props) {
  const [refreshingAll, setRefreshingAll] = useState(false);

  const handleRefreshAll = useCallback(async () => {
    setRefreshingAll(true);
    try {
      const res = await fetch("/api/data/freshness", { method: "POST" });
      const data = await res.json();
      if (res.ok && data.ok) {
        toast.success(data.message ?? "Semua data stale berhasil di-refresh");
        window.location.reload();
      } else {
        toast.error(data.error ?? "Gagal refresh");
      }
    } catch {
      toast.error("Gagal menghubungi server");
    } finally {
      setRefreshingAll(false);
    }
  }, []);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div className="flex gap-4 text-sm">
          <span className="text-muted">
            Total: <strong className="text-fg">{report.total_count}</strong>
          </span>
          <span className="text-emerald-400">
            Fresh: <strong>{report.fresh_count}</strong>
          </span>
          <span className="text-amber-400">
            Stale: <strong>{report.stale_count}</strong>
          </span>
        </div>
        {report.has_stale && (
          <button
            type="button"
            onClick={handleRefreshAll}
            disabled={refreshingAll}
            className="rounded bg-accent px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-accent/80 disabled:opacity-50"
          >
            {refreshingAll ? "Refreshing..." : "Run All Stale"}
          </button>
        )}
      </div>

      <CategorySection category="provider" label="Providers" report={report} />
      <CategorySection category="analysis" label="Analysis" report={report} />
      <CategorySection category="review" label="Review" report={report} />
    </div>
  );
}
```

- [ ] **Step 4: Create the Providers page**

```tsx
// apps/web/src/app/operations/providers/page.tsx
import { checkFreshness } from "@/lib/runtime";
import { OperationsTable } from "@/components/OperationsTable";

export const dynamic = "force-dynamic";

export default async function ProvidersPage() {
  let report;
  try {
    report = await checkFreshness();
  } catch {
    report = {
      fresh_count: 0,
      stale_count: 0,
      total_count: 0,
      has_stale: false,
      stale_types: [],
      records: [],
    };
  }

  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted">
        Monitor and run data operations. Status shows when each data type was last refreshed.
      </p>
      <OperationsTable report={report} />
    </div>
  );
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/OperationsTable.test.tsx --reporter=verbose`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/components/OperationsTable.tsx apps/web/src/components/OperationsTable.test.tsx apps/web/src/app/operations/providers/page.tsx
git commit -m "feat(s3): add OperationsTable component and Providers page"
```

---

### Task 7: HealthOverview Component + Health Page

**Files:**
- Create: `apps/web/src/components/HealthOverview.tsx`
- Create: `apps/web/src/app/operations/health/page.tsx`
- Test: `apps/web/src/components/HealthOverview.test.tsx`

**Depends on:** Task 2 (health API types), Task 5 (layout)

- [ ] **Step 1: Write the test**

```tsx
// apps/web/src/components/HealthOverview.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { HealthOverview } from "./HealthOverview";
import type { HealthReport } from "@/lib/health";

const MOCK_HEALTHY: HealthReport = {
  overall: "healthy",
  summary: "All required services available.",
  checks: {
    python: { status: "ok", label: "Core Engine", detail: "Python 3.12.7" },
    database: { status: "ok", label: "Database", detail: "Connected" },
    runtime: { status: "ok", label: "Runtime", detail: "Schema ready" },
    llm: { status: "ok", label: "LLM Provider", detail: "openrouter / claude" },
  },
  refresh_mode: "manual",
};

const MOCK_DEGRADED: HealthReport = {
  overall: "degraded",
  summary: "Some non-critical services unavailable.",
  checks: {
    python: { status: "ok", label: "Core Engine", detail: "Python 3.12.7" },
    database: { status: "ok", label: "Database", detail: "Connected" },
    runtime: { status: "ok", label: "Runtime", detail: "Schema ready" },
    llm: { status: "degraded", label: "LLM Provider", detail: "Not configured" },
  },
  refresh_mode: "manual",
};

describe("HealthOverview", () => {
  it("should show healthy status", () => {
    render(<HealthOverview report={MOCK_HEALTHY} />);
    expect(screen.getByText("Healthy")).toBeDefined();
    expect(screen.getByText("All required services available.")).toBeDefined();
  });

  it("should show degraded status", () => {
    render(<HealthOverview report={MOCK_DEGRADED} />);
    expect(screen.getByText("Degraded")).toBeDefined();
  });

  it("should show all system checks", () => {
    render(<HealthOverview report={MOCK_HEALTHY} />);
    expect(screen.getByText("Core Engine")).toBeDefined();
    expect(screen.getByText("Database")).toBeDefined();
    expect(screen.getByText("Runtime")).toBeDefined();
    expect(screen.getByText("LLM Provider")).toBeDefined();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/HealthOverview.test.tsx --reporter=verbose`
Expected: FAIL

- [ ] **Step 3: Write the component**

```tsx
// apps/web/src/components/HealthOverview.tsx
"use client";

import type { HealthReport, OverallStatus } from "@/lib/health";

const OVERALL_COLORS: Record<OverallStatus, { icon: string; bg: string; text: string }> = {
  healthy: { icon: "🟢", bg: "border-emerald-500/30 bg-emerald-500/10", text: "text-emerald-200" },
  degraded: { icon: "🟡", bg: "border-amber-500/30 bg-amber-500/10", text: "text-amber-200" },
  unhealthy: { icon: "🔴", bg: "border-red-500/30 bg-red-500/10", text: "text-red-200" },
};

const CHECK_COLORS: Record<string, string> = {
  ok: "text-emerald-400",
  degraded: "text-amber-400",
  fail: "text-red-400",
};

interface Props {
  report: HealthReport;
}

export function HealthOverview({ report }: Props) {
  const colors = OVERALL_COLORS[report.overall];

  return (
    <div className="flex flex-col gap-6">
      {/* Overall Status */}
      <div className={`rounded-md border p-5 ${colors.bg}`}>
        <div className="flex items-center gap-3">
          <span className="text-2xl">{colors.icon}</span>
          <div>
            <p className={`text-lg font-semibold capitalize ${colors.text}`}>
              {report.overall}
            </p>
            <p className="text-sm text-muted">{report.summary}</p>
          </div>
        </div>
      </div>

      {/* System Health */}
      <section>
        <h2 className="mb-3 text-xs uppercase tracking-widest text-muted">System Health</h2>
        <div className="grid gap-2">
          {Object.values(report.checks).map((check) => (
            <div
              key={check.label}
              className="flex items-center justify-between rounded-md border border-muted/30 bg-white/[0.02] px-4 py-3"
            >
              <span className="text-sm">{check.label}</span>
              <span className={`text-sm font-medium ${CHECK_COLORS[check.status] ?? "text-muted"}`}>
                {check.detail}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Data Refresh */}
      <section>
        <h2 className="mb-3 text-xs uppercase tracking-widest text-muted">Data Refresh</h2>
        <div className="rounded-md border border-muted/30 bg-white/[0.02] px-4 py-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">Mode</span>
            <span className="rounded border border-muted/40 px-2 py-0.5 text-[10px] uppercase tracking-widest text-muted">
              {report.refresh_mode}
            </span>
          </div>
          <p className="mt-2 text-xs text-muted">
            Refresh occurs through provider actions and stale-data banners. Automatic scheduling is planned.
          </p>
        </div>
      </section>

      {/* Raw JSON link */}
      <details className="rounded-md border border-muted/30 bg-white/[0.02]">
        <summary className="cursor-pointer px-4 py-2 text-xs font-medium text-muted hover:text-fg">
          View Full Health JSON
        </summary>
        <pre className="overflow-x-auto px-4 pb-3 pt-1 text-xs text-muted">
          {JSON.stringify(report, null, 2)}
        </pre>
      </details>
    </div>
  );
}
```

- [ ] **Step 4: Create the Health page**

Uses `runPython` directly (same pattern as `data-quality/page.tsx`) instead of internal fetch.

```tsx
// apps/web/src/app/operations/health/page.tsx
import { runPython } from "@/lib/pythonRunner";
import type { RuntimeStatus } from "@/lib/runtime";
import type { HealthReport, ComponentCheck, OverallStatus } from "@/lib/health";
import { HealthOverview } from "@/components/HealthOverview";

export const dynamic = "force-dynamic";

function makeCheck(status: "ok" | "degraded" | "fail", label: string, detail: string): ComponentCheck {
  return { status, label, detail };
}

function computeOverall(checks: HealthReport["checks"]): { overall: OverallStatus; summary: string } {
  const statuses = Object.values(checks).map((c) => c.status);
  if (statuses.some((s) => s === "fail")) return { overall: "unhealthy", summary: "Core services unavailable." };
  if (statuses.some((s) => s === "degraded")) return { overall: "degraded", summary: "Some non-critical services unavailable." };
  return { overall: "healthy", summary: "All required services available." };
}

export default async function HealthPage() {
  let runtime = { status: "fail" as const, python: "fail" as const, database: "fail" as const };
  let llmStatus: "ok" | "degraded" = "degraded";
  let llmDetail = "Could not check";

  try {
    const { data } = await runPython<RuntimeStatus>("scripts.runtime", {
      args: ["status", "--json"], timeoutMs: 30_000,
    });
    runtime = {
      status: data.schema_status === "ready" ? "ok" : "degraded",
      python: data.python_executable ? "ok" : "degraded",
      database: data.db_path ? "ok" : "fail",
    };
  } catch {
    // defaults to fail
  }

  try {
    const { data } = await runPython<{ ok: boolean; configured: boolean; provider: string; model: string }>(
      "scripts.llm_status", { args: ["--json"], timeoutMs: 15_000 },
    );
    if (data.configured) {
      llmStatus = "ok";
      llmDetail = `${data.provider} / ${data.model}`;
    } else {
      llmDetail = "Not configured";
    }
  } catch {
    llmDetail = "Could not verify";
  }

  const checks: HealthReport["checks"] = {
    python: makeCheck(runtime.python, "Core Engine", runtime.python === "ok" ? "Available" : "Unavailable"),
    database: makeCheck(runtime.database, "Database", runtime.database === "ok" ? "Ready" : "Not connected"),
    runtime: makeCheck(runtime.status, "Runtime", runtime.status === "ok" ? "Schema ready" : "Needs attention"),
    llm: makeCheck(llmStatus, "LLM Provider", llmDetail),
  };

  const { overall, summary } = computeOverall(checks);

  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted">
        System health overview. Check if all services are running correctly.
      </p>
      <HealthOverview report={{ overall, summary, checks, refresh_mode: "manual" }} />
    </div>
  );
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/HealthOverview.test.tsx --reporter=verbose`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/components/HealthOverview.tsx apps/web/src/components/HealthOverview.test.tsx apps/web/src/app/operations/health/page.tsx
git commit -m "feat(s3): add HealthOverview component and Health page"
```

---

### Task 8: Config Page

**Files:**
- Create: `apps/web/src/app/operations/config/page.tsx`

**Depends on:** Task 3 (config API), Task 5 (layout)

- [ ] **Step 1: Write the Config page**

```tsx
// apps/web/src/app/operations/config/page.tsx
import { LlmConfigForm } from "./LlmConfigForm";
import { AppConfigForm } from "./AppConfigForm";

export const dynamic = "force-dynamic";

export default function ConfigPage() {
  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted">
        Application configuration. Changes are saved to .env.local.
      </p>
      <LlmConfigForm />
      <AppConfigForm />
    </div>
  );
}
```

- [ ] **Step 2: Create LLM Config client component**

```tsx
// apps/web/src/app/operations/config/LlmConfigForm.tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

interface LlmConfig {
  provider: string;
  baseUrl: string;
  model: string;
}

const PROVIDERS = [
  { value: "anthropic", label: "Anthropic" },
  { value: "openai_compatible", label: "OpenAI Compatible" },
  { value: "openai", label: "OpenAI" },
  { value: "deepseek", label: "DeepSeek" },
  { value: "openrouter", label: "OpenRouter" },
  { value: "tokenrouter", label: "TokenRouter" },
  { value: "custom", label: "Custom" },
];

export function LlmConfigForm() {
  const [config, setConfig] = useState<LlmConfig | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("/api/config?section=llm")
      .then((r) => r.json())
      .then((data) => {
        setConfig(data.config);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleSave = useCallback(async () => {
    if (!config) return;
    setSaving(true);
    try {
      const body: Record<string, string> = {
        provider: config.provider,
        baseUrl: config.baseUrl,
        model: config.model,
      };
      if (apiKey) body.apiKey = apiKey;

      const res = await fetch("/api/config?section=llm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        toast.success("LLM configuration saved");
        setApiKey("");
      } else {
        toast.error(data.error ?? "Failed to save");
      }
    } catch {
      toast.error("Failed to save LLM configuration");
    } finally {
      setSaving(false);
    }
  }, [config, apiKey]);

  if (loading) return <Skeleton />;

  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <h2 className="text-sm font-medium">LLM Provider</h2>
      <p className="mt-1 text-xs text-muted">Configure the LLM used for AI brief, chat, and analysis features.</p>

      <div className="mt-4 grid gap-4">
        <div>
          <label className="text-xs uppercase tracking-widest text-muted">Provider</label>
          <select
            value={config?.provider ?? ""}
            onChange={(e) => setConfig((prev) => prev ? { ...prev, provider: e.target.value } : null)}
            className="mt-1 block w-full rounded border border-muted/30 bg-white/[0.04] px-3 py-2 text-sm text-fg"
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs uppercase tracking-widest text-muted">Model</label>
          <input
            type="text"
            value={config?.model ?? ""}
            onChange={(e) => setConfig((prev) => prev ? { ...prev, model: e.target.value } : null)}
            className="mt-1 block w-full rounded border border-muted/30 bg-white/[0.04] px-3 py-2 text-sm text-fg"
          />
        </div>

        <div>
          <label className="text-xs uppercase tracking-widest text-muted">Base URL</label>
          <input
            type="text"
            value={config?.baseUrl ?? ""}
            onChange={(e) => setConfig((prev) => prev ? { ...prev, baseUrl: e.target.value } : null)}
            className="mt-1 block w-full rounded border border-muted/30 bg-white/[0.04] px-3 py-2 text-sm text-fg"
          />
        </div>

        <div>
          <label className="text-xs uppercase tracking-widest text-muted">API Key</label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Leave empty to keep current key"
            className="mt-1 block w-full rounded border border-muted/30 bg-white/[0.04] px-3 py-2 text-sm text-fg"
          />
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !config}
            className="rounded bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent/80 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </section>
  );
}

function Skeleton() {
  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <div className="h-4 w-24 animate-pulse rounded bg-white/10" />
      <div className="mt-4 space-y-3">
        <div className="h-8 animate-pulse rounded bg-white/10" />
        <div className="h-8 animate-pulse rounded bg-white/10" />
        <div className="h-8 animate-pulse rounded bg-white/10" />
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Create App Config client component**

```tsx
// apps/web/src/app/operations/config/AppConfigForm.tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

interface AppConfig {
  dataDir: string;
}

const TIMEZONES = [
  "Asia/Jakarta",
  "Asia/Makassar",
  "Asia/Jayapura",
  "Asia/Singapore",
  "Asia/Hong_Kong",
  "Asia/Tokyo",
];

export function AppConfigForm() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [timezone, setTimezone] = useState("Asia/Jakarta");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/config?section=app")
      .then((r) => r.json())
      .then((data) => {
        setConfig(data.config);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return null;

  return (
    <section className="rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <h2 className="text-sm font-medium">Application</h2>
      <p className="mt-1 text-xs text-muted">General application settings.</p>

      <div className="mt-4 grid gap-4">
        <div>
          <label className="text-xs uppercase tracking-widest text-muted">Timezone</label>
          <select
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="mt-1 block w-full rounded border border-muted/30 bg-white/[0.04] px-3 py-2 text-sm text-fg"
          >
            {TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>{tz}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs uppercase tracking-widest text-muted">Data Directory</label>
          <input
            type="text"
            value={config?.dataDir ?? ""}
            readOnly
            className="mt-1 block w-full rounded border border-muted/30 bg-white/[0.04] px-3 py-2 text-sm text-muted"
          />
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/app/operations/config/page.tsx apps/web/src/app/operations/config/LlmConfigForm.tsx apps/web/src/app/operations/config/AppConfigForm.tsx
git commit -m "feat(s3): add Config page with LLM and App config forms"
```

---

### Task 9: Dashboard Card

**Files:**
- Modify: `apps/web/src/app/page.tsx`

**Depends on:** Nothing

- [ ] **Step 1: Add Operations card to dashboard**

```tsx
// apps/web/src/app/page.tsx — add to NAV array
const NAV = [
  // ... existing items ...
  { href: "/operations/providers", label: "Operations", desc: "Monitor health, run data operations, and manage configuration." },
  // ... keep other items ...
];
```

The exact edit:

```tsx
  { href: "/portfolio", label: "Portfolio", desc: "Review local positions with available prices." },
  { href: "/operations/providers", label: "Operations", desc: "Monitor health, run data operations, and manage configuration." },
];
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/app/page.tsx
git commit -m "feat(s3): add Operations card to dashboard navigation"
```

---

### Self-Review Checklist

1. **Spec coverage:** All 4 spec sections covered:
   - Task 5 → section 3.1 (layout)
   - Task 6 → section 3.2 (providers)
   - Task 7 → section 3.3 (health)
   - Task 8 → section 3.4 (config)
   - Task 2 → section 4.1 (health API)
   - Task 3 → section 4.2 (config API)
   - Task 4 → section 4.3 (run API)

2. **Placeholder scan:** All code blocks contain complete implementation code. No "TBD", "TODO", or "implement later".

3. **Type consistency:** Types are defined in Task 2 (`HealthReport`, `ComponentCheck`) and Task 1 (`Operation`, `OperationCategory`) and imported consistently across all tasks.
