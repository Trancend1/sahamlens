export type OperationCategory = "provider" | "analysis" | "review";

export interface Operation {
  id: string;
  name: string;
  description: string;
  category: OperationCategory;
  route: string;
  freshnessKey: string;
  timeoutMs: number;
}

export const OPERATIONS: Operation[] = [
  {
    id: "provider_health",
    name: "Provider Health",
    description: "Check data provider connectivity and freshness",
    category: "provider",
    route: "/api/operations/provider_health/run",
    freshnessKey: "provider_health",
    timeoutMs: 120_000,
  },
  {
    id: "prices",
    name: "Refresh Prices",
    description: "Ingest historical price data from watchlist",
    category: "provider",
    route: "/api/operations/prices/run",
    freshnessKey: "prices",
    timeoutMs: 180_000,
  },
  {
    id: "fundamentals",
    name: "Fundamentals",
    description: "Refresh fundamental snapshots from watchlist",
    category: "provider",
    route: "/api/operations/fundamentals/run",
    freshnessKey: "fundamentals",
    timeoutMs: 180_000,
  },
  {
    id: "news",
    name: "News",
    description: "Fetch and summarize news from RSS feeds",
    category: "provider",
    route: "/api/operations/news/run",
    freshnessKey: "news",
    timeoutMs: 180_000,
  },
  {
    id: "alerts",
    name: "Alerts",
    description: "Evaluate alert rules against current data",
    category: "analysis",
    route: "/api/operations/alerts/run",
    freshnessKey: "alerts",
    timeoutMs: 60_000,
  },
  {
    id: "screener",
    name: "Screener",
    description: "Run screening rules on watchlist",
    category: "analysis",
    route: "/api/operations/screener/run",
    freshnessKey: "screener",
    timeoutMs: 120_000,
  },
  {
    id: "strategy_rules",
    name: "Strategy Rules",
    description: "Evaluate strategy rule discipline checks",
    category: "review",
    route: "/api/operations/strategy_rules/run",
    freshnessKey: "strategy_rules",
    timeoutMs: 60_000,
  },
  {
    id: "weekly_review",
    name: "Weekly Review",
    description: "Generate weekly journal consistency review",
    category: "review",
    route: "/api/operations/weekly_review/run",
    freshnessKey: "weekly_review",
    timeoutMs: 120_000,
  },
];

export function getOperation(id: string): Operation | undefined {
  return OPERATIONS.find((op) => op.id === id);
}

export function getOperationsByCategory(): Record<OperationCategory, Operation[]> {
  const result: Record<OperationCategory, Operation[]> = {
    provider: [],
    analysis: [],
    review: [],
  };
  for (const op of OPERATIONS) {
    result[op.category].push(op);
  }
  return result;
}
