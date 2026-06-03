-- Migration 0006 - V1-S4 weekly journal review and simple strategy rules.

CREATE TABLE IF NOT EXISTS weekly_review_runs (
    review_id TEXT PRIMARY KEY,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('completed', 'partial', 'failed')
    ),
    journal_entry_count INTEGER NOT NULL DEFAULT 0,
    reviewed_plan_count INTEGER NOT NULL DEFAULT 0,
    rule_evaluation_count INTEGER NOT NULL DEFAULT 0,
    violation_count INTEGER NOT NULL DEFAULT 0,
    needs_data_count INTEGER NOT NULL DEFAULT 0,
    summary TEXT NOT NULL,
    evidence TEXT NOT NULL DEFAULT '[]',
    caveats TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weekly_review_findings (
    finding_id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL,
    finding_type TEXT NOT NULL CHECK (
        finding_type IN ('behavior_pattern', 'rule_violation', 'missing_data', 'risk_discipline', 'follow_up', 'caveat')
    ),
    title TEXT NOT NULL,
    detail TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (
        severity IN ('info', 'warning', 'critical')
    ),
    evidence TEXT NOT NULL DEFAULT '[]',
    caveats TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY (review_id) REFERENCES weekly_review_runs(review_id)
);

CREATE TABLE IF NOT EXISTS strategy_rules (
    rule_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    rule_category TEXT NOT NULL CHECK (
        rule_category IN ('journal_completeness', 'risk_discipline', 'plan_adherence', 'emotion_discipline', 'review_hygiene')
    ),
    required_fields TEXT NOT NULL DEFAULT '[]',
    violation_code TEXT NOT NULL,
    needs_data_behavior TEXT NOT NULL DEFAULT 'needs_data' CHECK (
        needs_data_behavior IN ('needs_data', 'skip')
    ),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS strategy_rule_evaluations (
    evaluation_id TEXT PRIMARY KEY,
    review_id TEXT,
    rule_id TEXT NOT NULL,
    journal_id BIGINT,
    symbol TEXT,
    evaluation_status TEXT NOT NULL CHECK (
        evaluation_status IN ('pass', 'fail', 'needs_data', 'skipped')
    ),
    evaluated_at TEXT NOT NULL,
    evidence TEXT NOT NULL DEFAULT '[]',
    caveats TEXT NOT NULL DEFAULT '[]',
    reason TEXT NOT NULL,
    FOREIGN KEY (review_id) REFERENCES weekly_review_runs(review_id),
    FOREIGN KEY (rule_id) REFERENCES strategy_rules(rule_id)
);

CREATE TABLE IF NOT EXISTS strategy_rule_violations (
    violation_id TEXT PRIMARY KEY,
    evaluation_id TEXT NOT NULL,
    review_id TEXT,
    rule_id TEXT NOT NULL,
    journal_id BIGINT,
    symbol TEXT,
    violation_code TEXT NOT NULL,
    violation_detail TEXT NOT NULL,
    evidence TEXT NOT NULL DEFAULT '[]',
    caveats TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY (evaluation_id) REFERENCES strategy_rule_evaluations(evaluation_id),
    FOREIGN KEY (review_id) REFERENCES weekly_review_runs(review_id),
    FOREIGN KEY (rule_id) REFERENCES strategy_rules(rule_id)
);
