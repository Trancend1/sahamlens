export interface HermesConfig {
  enabled: boolean;
  telegramConfigured: boolean;
  providerName: string;
  providerConfigured: boolean;
}

export interface ProcessState {
  running: boolean;
  pid: number | null;
}

export interface HermesStatus {
  config: HermesConfig;
  process: ProcessState;
}

export type ControlAction = "start" | "stop";

export interface ControlResult {
  ok: boolean;
  message: string;
}
