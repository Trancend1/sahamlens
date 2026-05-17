import { describe, expect, it, vi } from "vitest";
import {
  PythonRunnerError,
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
});
