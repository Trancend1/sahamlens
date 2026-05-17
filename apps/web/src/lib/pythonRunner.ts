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

function defaultPython(): string {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;
  return process.platform === "win32" ? "python" : "python3";
}
