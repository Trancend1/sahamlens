import { runPython } from "./pythonRunner";
import type { TradePlan } from "./journal-client";

export type {
  SetupType,
  TradeStatus,
  EmotionLevel,
  RiskFlag,
  CritiqueCategory,
  CritiqueStatus,
  TradePlan,
  CritiqueCheck,
  JournalCritique,
  PositionCalc,
} from "./journal-client";

export { calcPositionSize } from "./journal-client";

export async function fetchPlans(symbol?: string): Promise<TradePlan[]> {
  const args: string[] = ["plan", "list"];
  if (symbol) args.push("--symbol", symbol);
  const { data } = await runPython<TradePlan[]>("scripts.journal", { args });
  return data;
}
