-- Migration 0007 - V1-S6 local alerts, Telegram delivery attempts, and manual-first earnings.

CREATE TABLE IF NOT EXISTS alert_rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    rule_type TEXT NOT NULL CHECK (
        rule_type IN ('price_above', 'price_below', 'volume_above')
    ),
    ticker TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    archived_at TEXT
);

CREATE TABLE IF NOT EXISTS alert_evaluations (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('success', 'skipped_stale_data', 'skipped_low_confidence', 'failed_provider', 'failed_runtime', 'no_match')
    ),
    reason TEXT NOT NULL,
    data_freshness_status TEXT NOT NULL CHECK (
        data_freshness_status IN ('fresh', 'delayed', 'stale', 'failed', 'partial', 'unknown')
    ),
    confidence_status TEXT NOT NULL CHECK (
        confidence_status IN ('high', 'medium', 'low', 'none')
    ),
    matched INTEGER NOT NULL DEFAULT 0,
    details_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
);

CREATE TABLE IF NOT EXISTS alert_events (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    evaluation_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (
        severity IN ('info', 'warning', 'critical')
    ),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('new', 'acknowledged', 'dismissed', 'marked_false_positive', 'resolved')
    ),
    created_at TEXT NOT NULL,
    acknowledged_at TEXT,
    dismissed_at TEXT,
    false_positive_at TEXT,
    resolved_at TEXT,
    notes TEXT,
    FOREIGN KEY (rule_id) REFERENCES alert_rules(id),
    FOREIGN KEY (evaluation_id) REFERENCES alert_evaluations(id)
);

CREATE TABLE IF NOT EXISTS alert_delivery_attempts (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('disabled', 'skipped_not_configured', 'sent', 'failed')
    ),
    attempted_at TEXT NOT NULL,
    error_code TEXT,
    error_message TEXT,
    redacted_details_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (event_id) REFERENCES alert_events(id)
);

CREATE TABLE IF NOT EXISTS earnings_events (
    id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    period TEXT NOT NULL,
    event_date TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (
        source_type IN ('manual', 'local_note', 'imported_file', 'unknown')
    ),
    source_ref TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('planned', 'reported', 'summarized', 'archived')
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS earnings_summaries (
    id TEXT PRIMARY KEY,
    earnings_event_id TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    caveats TEXT NOT NULL DEFAULT '[]',
    input_snapshot_json TEXT NOT NULL DEFAULT '{}',
    confidence_status TEXT NOT NULL CHECK (
        confidence_status IN ('manual_only', 'partial_local_data', 'insufficient_data')
    ),
    FOREIGN KEY (earnings_event_id) REFERENCES earnings_events(id)
);

CREATE INDEX IF NOT EXISTS idx_alert_rules_ticker ON alert_rules(ticker);
CREATE INDEX IF NOT EXISTS idx_alert_rules_active ON alert_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_alert_rules_archived_at ON alert_rules(archived_at);
CREATE INDEX IF NOT EXISTS idx_alert_evaluations_rule_id ON alert_evaluations(rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_evaluations_status ON alert_evaluations(status);
CREATE INDEX IF NOT EXISTS idx_alert_evaluations_evaluated_at ON alert_evaluations(evaluated_at);
CREATE INDEX IF NOT EXISTS idx_alert_events_rule_id ON alert_events(rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_events_ticker ON alert_events(ticker);
CREATE INDEX IF NOT EXISTS idx_alert_events_status ON alert_events(status);
CREATE INDEX IF NOT EXISTS idx_alert_events_created_at ON alert_events(created_at);
CREATE INDEX IF NOT EXISTS idx_alert_delivery_attempts_event_id ON alert_delivery_attempts(event_id);
CREATE INDEX IF NOT EXISTS idx_alert_delivery_attempts_status ON alert_delivery_attempts(status);
CREATE INDEX IF NOT EXISTS idx_earnings_events_ticker ON earnings_events(ticker);
CREATE INDEX IF NOT EXISTS idx_earnings_events_status ON earnings_events(status);
CREATE INDEX IF NOT EXISTS idx_earnings_events_event_date ON earnings_events(event_date);
CREATE INDEX IF NOT EXISTS idx_earnings_summaries_event_id ON earnings_summaries(earnings_event_id);
