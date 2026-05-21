"""Model selector + daily cost circuit breaker.

`CostBudget` loaded from `config/cost_budget.yml` (falls back to `.example`).
`CircuitBreaker.check()` raises BudgetExceeded when projected daily spend hits the cap.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import duckdb
import yaml
from packages.core.news.repo import daily_ai_spend
from pydantic import BaseModel, Field

Task = Literal["news_summary", "daily_brief", "earnings", "journal_critique", "stock_chat"]

DEFAULT_BUDGET_PATH = Path("config/cost_budget.yml")
EXAMPLE_BUDGET_PATH = Path("config/cost_budget.example.yml")

DEFAULT_TASK_MODEL: dict[Task, str] = {
    "news_summary": "claude-haiku-4-5-20251001",
    "daily_brief": "claude-sonnet-4-6",
    "earnings": "claude-opus-4-7",
    "journal_critique": "claude-sonnet-4-6",
    "stock_chat": "claude-sonnet-4-6",
}


class BudgetExceeded(Exception):
    """Raised by CircuitBreaker when today's projected spend hits the cap."""


class CostBudget(BaseModel):
    daily_usd_cap: float = Field(gt=0)
    per_model_caps: dict[str, float] = Field(default_factory=dict)
    per_call_usd: dict[str, float] = Field(default_factory=dict)


def load_budget(path: Path | None = None) -> CostBudget:
    target = path or DEFAULT_BUDGET_PATH
    if not target.exists():
        target = EXAMPLE_BUDGET_PATH
    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    return CostBudget.model_validate(raw)


class ModelRouter:
    """Selects model id per task. Defaults overridable via constructor."""

    def __init__(self, *, overrides: dict[Task, str] | None = None) -> None:
        self._mapping: dict[Task, str] = {**DEFAULT_TASK_MODEL, **(overrides or {})}

    def select(self, task: Task) -> str:
        return self._mapping[task]


class CircuitBreaker:
    """Trips when today's projected spend >= cap. Spend = ai_log rows x per_call_usd."""

    def __init__(self, budget: CostBudget, *, clock: type[datetime] = datetime) -> None:
        self._budget = budget
        self._clock = clock

    def check(self, conn: duckdb.DuckDBPyConnection, model: str) -> None:
        today_iso = self._clock.now(UTC).date().isoformat()
        calls_today = daily_ai_spend(conn, day_iso=today_iso)
        per_call = self._budget.per_call_usd.get(model, 0.005)
        projected = (calls_today + 1) * per_call
        cap = self._budget.per_model_caps.get(model, self._budget.daily_usd_cap)
        if projected > min(cap, self._budget.daily_usd_cap):
            raise BudgetExceeded(
                f"model={model} projected={projected:.4f} > cap={cap:.4f} (calls_today={calls_today})"
            )
