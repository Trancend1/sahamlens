import { runPython } from "./pythonRunner";

export interface PortfolioPosition {
  symbol: string;
  lots: number;
  avg_price: number;
  imported_at: string;
  source: "csv" | "manual";
}

export interface ImportResult {
  positions: PortfolioPosition[];
  warnings: string[];
  field_map: Record<string, string>;
  detected_columns: string[];
}

export async function fetchPositions(): Promise<PortfolioPosition[]> {
  const { data } = await runPython<PortfolioPosition[]>("scripts.portfolio", {
    args: ["list"],
  });
  return data;
}
