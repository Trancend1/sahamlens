import { execFile, type ExecFileOptions } from "node:child_process";
import path from "node:path";

const DEFAULT_TIMEOUT_MS = 15_000;

export interface RunOptions {
  args?: readonly string[];
  cwd?: string;
  timeoutMs?: number;
  python?: string;
}

export interface RunResult<T> {
  data: T;
  rawStdout: string;
  rawStderr: string;
}

export interface ExecResult {
  stdout: string;
  stderr: string;
}

export type ExecFn = (cmd: string, args: readonly string[], opts: ExecFileOptions) => Promise<ExecResult>;

export interface RunDeps {
  exec?: ExecFn;
}

export type RuntimeErrorCode =
  | "schema_stale"
  | "missing_table"
  | "python_not_found"
  | "db_locked"
  | "empty_data"
  | "command_failed";

export interface RuntimeErrorInfo {
  code: RuntimeErrorCode;
  message: string;
  details: string;
  recommended_command: string | null;
}

export class PythonRunnerError extends Error {
  constructor(
    message: string,
    public readonly stdout: string,
    public readonly stderr: string,
    public readonly exitCode: number | null,
  ) {
    super(message);
    this.name = "PythonRunnerError";
  }
}

export class RuntimeFetchError extends Error {
  constructor(public readonly info: RuntimeErrorInfo) {
    super(info.message);
    this.name = "RuntimeFetchError";
  }
}

function repoRoot(): string {
  return path.resolve(process.cwd(), "..", "..");
}

const defaultExec: ExecFn = (cmd, args, opts) =>
  new Promise((resolve, reject) => {
    const optsWithUtf8 = { ...opts, encoding: "utf8" as BufferEncoding };
    execFile(cmd, args as string[], optsWithUtf8, (err, stdout, stderr) => {
      const out = (stdout as unknown as string) ?? "";
      const errOut = (stderr as unknown as string) ?? "";
      if (err) {
        const e = err as NodeJS.ErrnoException & { code?: number | string | null };
        const exit = typeof e.code === "number" ? e.code : null;
        reject(new PythonRunnerError(e.message, out, errOut, exit));
        return;
      }
      resolve({ stdout: out, stderr: errOut });
    });
  });

export async function runPython<T = unknown>(
  module: string,
  options: RunOptions = {},
  deps: RunDeps = {},
): Promise<RunResult<T>> {
  const exec = deps.exec ?? defaultExec;
  const cwd = options.cwd ?? repoRoot();
  const python = options.python ?? defaultPython();
  const args = ["-m", module, ...(options.args ?? [])];
  const timeout = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  const { stdout, stderr } = await exec(python, args, {
    cwd,
    timeout,
    maxBuffer: 4 * 1024 * 1024,
    windowsHide: true,
  });
  const data = parseJson<T>(stdout, stderr);
  return { data, rawStdout: stdout, rawStderr: stderr };
}

function parseJson<T>(stdout: string, stderr: string): T {
  const trimmed = stdout.trim();
  if (!trimmed) {
    throw new PythonRunnerError("python returned empty stdout", stdout, stderr, 0);
  }
  try {
    return JSON.parse(trimmed) as T;
  } catch (err) {
    const e = err as Error;
    throw new PythonRunnerError(`invalid JSON from python: ${e.message}`, stdout, stderr, 0);
  }
}

export function toRuntimeFetchError(error: unknown): RuntimeFetchError {
  if (error instanceof RuntimeFetchError) return error;
  return new RuntimeFetchError(classifyPythonRunnerError(error));
}

export function normalizeRuntimeError(error: unknown): RuntimeErrorInfo {
  if (error instanceof RuntimeFetchError) return error.info;
  return classifyPythonRunnerError(error);
}

export function classifyPythonRunnerError(error: unknown): RuntimeErrorInfo {
  if (!(error instanceof PythonRunnerError)) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      code: "command_failed",
      message: "Runtime command failed.",
      details: sanitizeDetails(message),
      recommended_command: null,
    };
  }

  const structured = parseStructuredRuntimeError(error.stdout);
  if (structured) return structured;

  const combined = `${error.message}\n${error.stderr}\n${error.stdout}`;
  const missingTable = combined.match(/Table with name\s+([A-Za-z0-9_]+)\s+does not exist/i);
  if (missingTable?.[1]) {
    const table = missingTable[1];
    return {
      code: "missing_table",
      message: `Missing runtime table: ${table}.`,
      details: "Local schema is stale or migration has not been applied.",
      recommended_command: "uv run python -m scripts.migrate",
    };
  }
  const sqliteMissingTable = combined.match(/no such table:\s*([A-Za-z0-9_]+)/i);
  if (sqliteMissingTable?.[1]) {
    const table = sqliteMissingTable[1];
    return {
      code: "missing_table",
      message: `Missing runtime table: ${table}.`,
      details: "Local schema is stale or migration has not been applied.",
      recommended_command: "uv run python -m scripts.migrate",
    };
  }

  if (/Catalog Error/i.test(combined) && /does not exist/i.test(combined)) {
    return {
      code: "schema_stale",
      message: "Local schema is stale.",
      details: "A required table or schema object is missing.",
      recommended_command: "uv run python -m scripts.migrate",
    };
  }

  if (/ENOENT|not recognized|No such file or directory/i.test(combined)) {
    return {
      code: "python_not_found",
      message: "Python executable was not found.",
      details: "Set PYTHON_BIN to the project virtualenv Python before starting the web app.",
      recommended_command: '$env:PYTHON_BIN=(Resolve-Path ".venv/Scripts/python.exe").Path',
    };
  }

  if (/lock|locked|Conflicting lock|IO Error/i.test(combined)) {
    return {
      code: "db_locked",
      message: "Local DuckDB file is locked.",
      details: "Close other commands using the same DuckDB file, then retry sequentially.",
      recommended_command: null,
    };
  }

  if (error.message.includes("empty stdout")) {
    return {
      code: "empty_data",
      message: "Runtime command returned no JSON data.",
      details: "The command completed without a structured payload.",
      recommended_command: null,
    };
  }

  return {
    code: "command_failed",
    message: "Runtime command failed.",
    details: sanitizeDetails(error.stderr || error.message),
    recommended_command: null,
  };
}

function parseStructuredRuntimeError(stdout: string): RuntimeErrorInfo | null {
  if (!stdout.trim()) return null;
  try {
    const parsed = JSON.parse(stdout) as {
      status?: string;
      errors?: Array<{ code?: string; message?: string; details?: unknown }>;
      recommended_commands?: string[];
    };
    const first = parsed.errors?.[0];
    if (!first || !isRuntimeErrorCode(first.code)) return null;
    const code = first.code;
    {
      const details =
        typeof first.details === "string"
          ? first.details
          : first.details
            ? JSON.stringify(first.details)
            : "No additional details.";
      return {
        code,
        message: first.message || "Runtime command failed.",
        details: sanitizeDetails(details),
        recommended_command: parsed.recommended_commands?.[0] ?? null,
      };
    }
  } catch {
    return null;
  }
  return null;
}

function isRuntimeErrorCode(value: unknown): value is RuntimeErrorCode {
  return (
    value === "schema_stale" ||
    value === "missing_table" ||
    value === "python_not_found" ||
    value === "db_locked" ||
    value === "empty_data" ||
    value === "command_failed"
  );
}

function sanitizeDetails(raw: string): string {
  const lines = raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !line.startsWith("Traceback"))
    .filter((line) => !line.startsWith("File "))
    .filter((line) => !line.startsWith("LINE "));
  return lines.slice(0, 4).join(" ") || "No additional details.";
}

function defaultPython(): string {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;
  return process.platform === "win32" ? "python" : "python3";
}
