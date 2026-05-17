"""yfinance adapter — IDX EOD OHLCV via `yfinance.Ticker(...).history(...)`.

Rate limit policy: 1 req / 0.5s sequential, exponential backoff 1→2→4→8s on 429.
See DATA_SOURCES.md §4.
"""

from packages.core.data_sources.yfinance.adapter import YFinanceSource

__all__ = ["YFinanceSource"]
