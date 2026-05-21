import { runPython } from "./pythonRunner";

export type EvidenceType = "price" | "indicator" | "news" | "fundamental" | "journal";

export interface EvidenceItem {
  type: EvidenceType;
  value: string;
  source_ref: string;
  freshness: string;
}

export interface StockBrief {
  symbol: string;
  analysis_date: string;
  prompt_template_id: string;
  model: string;
  evidence: EvidenceItem[];
  bullish_view: string;
  bearish_view: string;
  uncertainty: string;
  caveats: string[];
  beginner_explanation: string;
  suggested_next_question: string;
  not_financial_advice: boolean;
}

export interface ChatResponse {
  question: string;
  answer: string;
  evidence: EvidenceItem[];
  caveats: string[];
  not_financial_advice: boolean;
}

export async function fetchBrief(symbol: string): Promise<StockBrief> {
  const { data } = await runPython<StockBrief>("scripts.generate_brief", {
    args: ["brief", "--symbol", symbol],
    timeoutMs: 60_000,
  });
  return data;
}

export async function askQuestion(
  symbol: string,
  question: string,
): Promise<ChatResponse> {
  const { data } = await runPython<ChatResponse>("scripts.generate_brief", {
    args: ["chat", "--symbol", symbol, "--question", question],
    timeoutMs: 60_000,
  });
  return data;
}
