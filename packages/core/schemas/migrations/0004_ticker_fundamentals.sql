-- Migration 0004 - V1-S2 ticker lifecycle, source coverage, and fundamentals.

CREATE TABLE IF NOT EXISTS ticker_lifecycle (
    symbol TEXT PRIMARY KEY,
    lifecycle_status TEXT NOT NULL CHECK (
        lifecycle_status IN ('active', 'suspended', 'delisted', 'renamed', 'unknown')
    ),
    coverage_tier TEXT NOT NULL CHECK (
        coverage_tier IN ('tier_a', 'tier_b', 'tier_c')
    ),
    lifecycle_source TEXT NOT NULL,
    coverage_source TEXT NOT NULL,
    last_verified_at TEXT NOT NULL,
    renamed_from TEXT,
    renamed_to TEXT,
    missing_data_reason TEXT,
    screener_eligible INTEGER NOT NULL DEFAULT 0,
    alert_eligible INTEGER NOT NULL DEFAULT 0,
    ai_explanation_eligible INTEGER NOT NULL DEFAULT 0,
    eligibility_reason TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_coverage (
    symbol TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (
        source_type IN ('ohlcv', 'fundamental', 'news', 'delivery', 'manual', 'other')
    ),
    provider_trust_tier TEXT NOT NULL CHECK (
        provider_trust_tier IN ('tier_1', 'tier_2', 'tier_3', 'tier_4')
    ),
    availability_state TEXT NOT NULL CHECK (
        availability_state IN ('available', 'partial', 'missing', 'failed', 'unknown')
    ),
    freshness_state TEXT NOT NULL CHECK (
        freshness_state IN ('fresh', 'delayed', 'stale', 'failed', 'partial', 'unknown')
    ),
    last_success_at TEXT,
    last_checked_at TEXT NOT NULL,
    missing_reason TEXT,
    coverage_count INTEGER,
    PRIMARY KEY (symbol, provider_name, source_type)
);

CREATE TABLE IF NOT EXISTS fundamental_snapshots (
    symbol TEXT NOT NULL,
    period TEXT NOT NULL,
    statement_date TEXT,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (
        source_type IN ('manual', 'official', 'public_provider', 'other')
    ),
    fetched_at TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    data_fields TEXT NOT NULL DEFAULT '{}',
    available_fields TEXT NOT NULL DEFAULT '[]',
    missing_fields TEXT NOT NULL DEFAULT '[]',
    completeness_state TEXT NOT NULL CHECK (
        completeness_state IN ('complete', 'partial', 'sparse', 'missing')
    ),
    confidence_level TEXT NOT NULL CHECK (
        confidence_level IN ('high', 'medium', 'low', 'none')
    ),
    confidence_score REAL,
    caveat TEXT,
    reason TEXT,
    PRIMARY KEY (symbol, period, source, fetched_at)
);
