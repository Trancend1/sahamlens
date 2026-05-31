-- Migration 0003 - provider health foundation for V1 data quality.

CREATE TABLE IF NOT EXISTS provider_health (
    provider_name TEXT NOT NULL,
    provider_trust_tier TEXT NOT NULL,
    source_type TEXT NOT NULL,
    freshness_state TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_success_at TEXT,
    last_failure_at TEXT,
    last_failure_reason TEXT,
    consecutive_failure_count INTEGER NOT NULL DEFAULT 0,
    coverage_count INTEGER,
    PRIMARY KEY (provider_name, source_type)
);
