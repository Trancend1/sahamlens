export type SetupType =
  | "ma_cross"
  | "breakout"
  | "mean_reversion"
  | "support_bounce"
  | "other";

export type TradeStatus = "planned" | "open" | "closed" | "skipped";

export type EmotionLevel = "calm" | "excited" | "fearful" | "greedy" | "uncertain";

export type RiskFlag = "green" | "amber" | "red" | "incomplete";

export type CritiqueCategory =
  | "thesis"
  | "invalidation"
  | "risk"
  | "catalyst"
  | "emotion"
  | "liquidity";

export type CritiqueStatus = "ok" | "weak" | "missing";

export interface TradePlan {
  id: number;
  symbol: string;
  setup_type: SetupType;
  thesis: string;
  entry_plan: string;
  stop_level: number;
  invalidation: string;
  target: string;
  position_size_rupiah: number;
  max_loss_rupiah: number;
  emotion: EmotionLevel | null;
  status: TradeStatus;
  result_rupiah: number | null;
  lesson: string | null;
  created_at: string;
  reviewed_at: string | null;
}

export interface CritiqueCheck {
  category: CritiqueCategory;
  status: CritiqueStatus;
  finding: string;
  suggested_question: string;
}

export interface JournalCritique {
  plan_id: number;
  checks: CritiqueCheck[];
  overall_risk_flag: RiskFlag;
  caveats: string[];
  not_financial_advice: boolean;
}

export interface PositionCalc {
  lots: number;
  positionSizeRupiah: number;
  maxLossRupiah: number;
  riskRupiah: number;
}

export function calcPositionSize(
  portfolioValue: number,
  riskPercent: number,
  entryPrice: number,
  stopPrice: number,
): PositionCalc {
  const riskRupiah = Math.floor(portfolioValue * riskPercent);
  if (riskPercent <= 0 || stopPrice >= entryPrice || entryPrice <= 0) {
    return { lots: 0, positionSizeRupiah: 0, maxLossRupiah: 0, riskRupiah };
  }
  const priceDiff = entryPrice - stopPrice;
  const riskPerLot = priceDiff * 100;
  const maxLots = Math.floor(riskRupiah / riskPerLot);
  return {
    lots: maxLots,
    positionSizeRupiah: Math.floor(maxLots * entryPrice * 100),
    maxLossRupiah: Math.floor(maxLots * riskPerLot),
    riskRupiah,
  };
}
