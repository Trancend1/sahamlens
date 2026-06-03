import { describe, expect, it, vi } from "vitest";
import {
  PythonRunnerError,
  classifyPythonRunnerError,
  runPython,
  type ExecFn,
  type ExecResult,
} from "./pythonRunner";

function okExec(stdout: string, stderr = ""): ExecFn {
  return vi.fn().mockResolvedValue({ stdout, stderr } as ExecResult);
}

function failExec(message: string, exitCode: number, stdout = "", stderr = ""): ExecFn {
  return vi.fn().mockRejectedValue(new PythonRunnerError(message, stdout, stderr, exitCode));
}

describe("runPython", () => {
  it("parses JSON stdout into typed result", async () => {
    const exec = okExec('{"hello":"world","n":1}');
    const result = await runPython<{ hello: string; n: number }>("dummy", {}, { exec });

    expect(result.data).toEqual({ hello: "world", n: 1 });
    expect(exec).toHaveBeenCalledTimes(1);
  });

  it("propagates PythonRunnerError on non-zero exit", async () => {
    const exec = failExec("nonzero exit", 1, "", "boom");
    await expect(runPython("dummy", {}, { exec })).rejects.toBeInstanceOf(PythonRunnerError);
  });

  it("throws PythonRunnerError on empty stdout", async () => {
    const exec = okExec("   ");
    await expect(runPython("dummy", {}, { exec })).rejects.toBeInstanceOf(PythonRunnerError);
  });

  it("throws PythonRunnerError on invalid JSON", async () => {
    const exec = okExec("not-json");
    await expect(runPython("dummy", {}, { exec })).rejects.toBeInstanceOf(PythonRunnerError);
  });

  it("maps malformed JSON from CLI to command_failed", async () => {
    const exec = okExec("not-json", "warning from cli");

    try {
      await runPython("dummy", {}, { exec });
      throw new Error("expected runPython to fail");
    } catch (err) {
      const runtimeError = classifyPythonRunnerError(err);
      expect(runtimeError.code).toBe("command_failed");
      expect(runtimeError.message).toContain("Runtime command failed");
    }
  });

  it("forwards args to python module invocation", async () => {
    const exec = vi.fn().mockResolvedValue({ stdout: "[]", stderr: "" } as ExecResult);
    await runPython("scripts.watchlist", { args: ["--json", "list"] }, { exec });

    const firstCall = exec.mock.calls[0];
    expect(firstCall).toBeDefined();
    const passedArgs = firstCall?.[1] as string[];
    expect(passedArgs).toEqual(["-m", "scripts.watchlist", "--json", "list"]);
  });

  it("passes python binary from options when provided", async () => {
    const exec = vi.fn().mockResolvedValue({ stdout: "0", stderr: "" } as ExecResult);
    await runPython("dummy", { python: "uv" }, { exec });

    expect(exec.mock.calls[0]?.[0]).toBe("uv");
  });

  it("classifies DuckDB missing-table tracebacks as missing_table without exposing raw trace", () => {
    const error = new PythonRunnerError(
      "Command failed: python -m scripts.journal_review",
      "",
      `_duckdb.CatalogException: Catalog Error: Table with name weekly_review_runs does not exist!
LINE 5:         FROM weekly_review_runs`,
      1,
    );

    const runtimeError = classifyPythonRunnerError(error);

    expect(runtimeError.code).toBe("missing_table");
    expect(runtimeError.message).toContain("weekly_review_runs");
    expect(runtimeError.recommended_command).toBe("uv run python -m scripts.migrate");
    expect(runtimeError.details).not.toContain("Traceback");
  });

  it("classifies generic schema stale errors", () => {
    const error = new PythonRunnerError(
      "Command failed",
      "",
      "Catalog Error: View with name schema_migrations does not exist",
      1,
    );

    const runtimeError = classifyPythonRunnerError(error);

    expect(runtimeError.code).toBe("schema_stale");
    expect(runtimeError.recommended_command).toBe("uv run python -m scripts.migrate");
  });

  it("classifies SQLite-style missing table errors without exposing raw no such table copy", () => {
    const error = new PythonRunnerError(
      "Command failed",
      "",
      "sqlite3.OperationalError: no such table: weekly_review_runs",
      1,
    );

    const runtimeError = classifyPythonRunnerError(error);

    expect(runtimeError.code).toBe("missing_table");
    expect(runtimeError.message).toContain("weekly_review_runs");
    expect(runtimeError.details).not.toContain("no such table");
    expect(runtimeError.details).not.toContain("sqlite3.OperationalError");
  });

  it("classifies missing python executable as python_not_found", () => {
    const error = new PythonRunnerError("spawn python ENOENT", "", "", null);

    const runtimeError = classifyPythonRunnerError(error);

    expect(runtimeError.code).toBe("python_not_found");
    expect(runtimeError.recommended_command).toContain("PYTHON_BIN");
  });

  it("classifies locked database errors with retry guidance", () => {
    const error = new PythonRunnerError(
      "Command failed",
      "",
      "IO Error: Could not set lock on file data/private/sahamlens.duckdb",
      1,
    );

    const runtimeError = classifyPythonRunnerError(error);

    expect(runtimeError.code).toBe("db_locked");
    expect(runtimeError.details).toContain("retry sequentially");
  });

  it("classifies empty stdout as empty_data", () => {
    const error = new PythonRunnerError("python returned empty stdout", "", "", 0);

    const runtimeError = classifyPythonRunnerError(error);

    expect(runtimeError.code).toBe("empty_data");
  });

  it("sanitizes long stderr, tracebacks, and internal file paths", () => {
    const error = new PythonRunnerError(
      "Command failed",
      "",
      [
        "Traceback (most recent call last):",
        'File "D:\\DevSpace\\Projects\\sahamlens\\scripts\\journal_review.py", line 178, in <module>',
        "RuntimeError: first useful line",
        "second useful line",
        "third useful line",
        "fourth useful line",
        "fifth useful line",
      ].join("\n"),
      1,
    );

    const runtimeError = classifyPythonRunnerError(error);

    expect(runtimeError.code).toBe("command_failed");
    expect(runtimeError.details).toContain("first useful line");
    expect(runtimeError.details).not.toContain("Traceback");
    expect(runtimeError.details).not.toContain("D:\\DevSpace");
    expect(runtimeError.details).not.toContain("fifth useful line");
  });
});
