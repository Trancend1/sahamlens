-- Migration 0005 - V1-S3 transparent screener rules and results.

CREATE TABLE IF NOT EXISTS screener_rules (
    rule_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    required_fields TEXT NOT NULL DEFAULT '[]',
    required_source_types TEXT NOT NULL DEFAULT '[]',
    min_coverage_tier TEXT NOT NULL CHECK (
        min_coverage_tier IN ('tier_a', 'tier_b', 'tier_c')
    ),
    allowed_freshness_states TEXT NOT NULL DEFAULT '["fresh","delayed"]',
    min_fundamental_completeness TEXT CHECK (
        min_fundamental_completeness IN ('complete', 'partial', 'sparse', 'missing')
    ),
    min_confidence_level TEXT CHECK (
        min_confidence_level IN ('high', 'medium', 'low', 'none')
    ),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS screener_rule_conditions (
    condition_id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    operator TEXT NOT NULL CHECK (
        operator IN ('gt', 'gte', 'lt', 'lte', 'eq', 'neq', 'exists', 'between')
    ),
    value_json TEXT,
    required_source_type TEXT CHECK (
        required_source_type IN ('ohlcv', 'fundamental', 'news', 'delivery', 'manual', 'other')
    ),
    missing_behavior TEXT NOT NULL DEFAULT 'exclude' CHECK (
        missing_behavior IN ('exclude', 'caveat')
    ),
    description TEXT,
    FOREIGN KEY (rule_id) REFERENCES screener_rules(rule_id)
);

CREATE TABLE IF NOT EXISTS screener_runs (
    run_id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('running', 'completed', 'failed', 'partial')
    ),
    universe_count INTEGER NOT NULL DEFAULT 0,
    included_count INTEGER NOT NULL DEFAULT 0,
    excluded_count INTEGER NOT NULL DEFAULT 0,
    data_quality_snapshot TEXT NOT NULL DEFAULT '{}',
    notes TEXT,
    FOREIGN KEY (rule_id) REFERENCES screener_rules(rule_id)
);

CREATE TABLE IF NOT EXISTS screener_results (
    run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    result_status TEXT NOT NULL CHECK (
        result_status IN ('included', 'excluded')
    ),
    coverage_tier TEXT NOT NULL CHECK (
        coverage_tier IN ('tier_a', 'tier_b', 'tier_c')
    ),
    lifecycle_status TEXT NOT NULL CHECK (
        lifecycle_status IN ('active', 'suspended', 'delisted', 'renamed', 'unknown')
    ),
    freshness_state TEXT NOT NULL CHECK (
        freshness_state IN ('fresh', 'delayed', 'stale', 'failed', 'partial', 'unknown')
    ),
    completeness_state TEXT CHECK (
        completeness_state IN ('complete', 'partial', 'sparse', 'missing')
    ),
    confidence_level TEXT CHECK (
        confidence_level IN ('high', 'medium', 'low', 'none')
    ),
    matched_conditions TEXT NOT NULL DEFAULT '[]',
    failed_conditions TEXT NOT NULL DEFAULT '[]',
    missing_fields TEXT NOT NULL DEFAULT '[]',
    exclusion_reasons TEXT NOT NULL DEFAULT '[]',
    caveats TEXT NOT NULL DEFAULT '[]',
    explanation TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,
    PRIMARY KEY (run_id, symbol),
    FOREIGN KEY (run_id) REFERENCES screener_runs(run_id)
);

CREATE TABLE IF NOT EXISTS screener_result_exclusions (
    run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    reason_detail TEXT NOT NULL,
    source_field TEXT,
    PRIMARY KEY (run_id, symbol, reason_code, source_field),
    FOREIGN KEY (run_id, symbol) REFERENCES screener_results(run_id, symbol)
);
