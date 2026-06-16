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

export interface FreshnessRecord {
  data_type: string;
  status: "fresh" | "stale" | "unknown";
  last_refreshed_at: string | null;
  age_seconds: number | null;
  threshold_seconds: number;
}

export interface FreshnessReport {
  fresh_count: number;
  stale_count: number;
  total_count: number;
  has_stale: boolean;
  stale_types: string[];
  records: FreshnessRecord[];
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

export async function checkFreshness(): Promise<FreshnessReport> {
  try {
    const { data } = await runPython<FreshnessReport>("scripts.freshness", {
      args: ["check", "--json"],
      timeoutMs: 15_000,
    });
    return data;
  } catch (err) {
    throw toRuntimeFetchError(err);
  }
}
