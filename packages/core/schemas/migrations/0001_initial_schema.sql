-- Migration 0001 — initial schema
-- Mirror ARCHITECTURE.md §6. Edit di sini, bukan di file derived.

CREATE TABLE IF NOT EXISTS stocks (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS price_history (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume BIGINT,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS watchlist (
    symbol TEXT PRIMARY KEY,
    tag TEXT,
    note TEXT,
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journal (
    id BIGINT PRIMARY KEY,
    symbol TEXT,
    setup_type TEXT,
    thesis TEXT,
    entry_plan TEXT,
    stop_level REAL,
    invalidation TEXT,
    target TEXT,
    position_size_rupiah BIGINT,
    max_loss_rupiah BIGINT,
    emotion TEXT,
    status TEXT,
    result_rupiah BIGINT,
    lesson TEXT,
    created_at TEXT NOT NULL,
    reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS portfolio_position (
    symbol TEXT,
    lots INTEGER,
    avg_price REAL,
    imported_at TEXT,
    source TEXT,
    PRIMARY KEY (symbol, imported_at)
);

CREATE TABLE IF NOT EXISTS news (
    id BIGINT PRIMARY KEY,
    url TEXT UNIQUE,
    title TEXT,
    source TEXT,
    published_at TEXT,
    summary TEXT,
    affected_tickers TEXT,
    sentiment_label TEXT,
    fetched_at TEXT
);

CREATE TABLE IF NOT EXISTS ai_log (
    id BIGINT PRIMARY KEY,
    prompt_template_id TEXT,
    model TEXT,
    input_context TEXT,
    output TEXT,
    confidence REAL,
    caveats_count INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS indicator_cache (
    symbol TEXT,
    date TEXT,
    indicator TEXT,
    value REAL,
    PRIMARY KEY (symbol, date, indicator)
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);
