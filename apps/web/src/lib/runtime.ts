import { runPython, toRuntimeFetchError } from "./pythonRunner";

export type SchemaStatus = "ready" | "stale" | "missing" | "unknown";

export interface RuntimeWarning {
  code: string;
  message: string;
  recommended_command: string | null;
}

export interface RuntimeStatus {
  ok: boolean;
  status: SchemaStatus;
  db_path: string;
  python_executable: string;
  applied_migrations: string[];
  pending_migrations: string[];
  missing_tables: string[];
  schema_status: SchemaStatus;
  warnings: RuntimeWarning[];
  errors: RuntimeWarning[];
  recommended_commands: string[];
}

export async function fetchRuntimeStatus(): Promise<RuntimeStatus> {
  try {
    const { data } = await runPython<RuntimeStatus>("scripts.runtime", {
      args: ["status", "--json"],
      timeoutMs: 30_000,
    });
    return data;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}
