-- Migration 0008 - V2 agentic research layer runtime audit + research queue (ADR-0019 D4).
-- agent_log: one row per agent interaction (separate from ai_log, which stays per LLM call).
-- agent_write_action: one row per write attempt, for manual confirmation + idempotency.
-- research_queue: owner research items captured from chat. Local private DB only.

CREATE TABLE IF NOT EXISTS agent_log (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    surface TEXT NOT NULL CHECK (
        surface IN ('telegram', 'discord', 'cli')
    ),
    intent TEXT NOT NULL,
    command_text_redacted TEXT NOT NULL DEFAULT '',
    ai_log_id BIGINT,
    context_scope TEXT NOT NULL DEFAULT 'none' CHECK (
        context_scope IN ('none', 'aggregate', 'journal_digest', 'ticker', 'alert', 'research', 'mixed')
    ),
    redaction_applied INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (ai_log_id) REFERENCES ai_log(id)
);

CREATE TABLE IF NOT EXISTS agent_write_action (
    id TEXT PRIMARY KEY,
    agent_log_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (
        action IN ('acknowledge_alert', 'mark_false_positive', 'save_journal_draft', 'add_research_item')
    ),
    target_ref TEXT,
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending_confirmation' CHECK (
        status IN ('pending_confirmation', 'confirmed', 'applied', 'rejected', 'expired')
    ),
    confirmed_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (agent_log_id) REFERENCES agent_log(id)
);

CREATE TABLE IF NOT EXISTS research_queue (
    id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    note TEXT NOT NULL,
    source_surface TEXT NOT NULL CHECK (
        source_surface IN ('telegram', 'discord', 'cli', 'web')
    ),
    status TEXT NOT NULL DEFAULT 'open' CHECK (
        status IN ('open', 'in_review', 'done', 'dropped')
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_log_session_id ON agent_log(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_log_surface ON agent_log(surface);
CREATE INDEX IF NOT EXISTS idx_agent_log_intent ON agent_log(intent);
CREATE INDEX IF NOT EXISTS idx_agent_log_created_at ON agent_log(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_write_action_agent_log_id ON agent_write_action(agent_log_id);
CREATE INDEX IF NOT EXISTS idx_agent_write_action_action ON agent_write_action(action);
CREATE INDEX IF NOT EXISTS idx_agent_write_action_status ON agent_write_action(status);
CREATE INDEX IF NOT EXISTS idx_research_queue_ticker ON research_queue(ticker);
CREATE INDEX IF NOT EXISTS idx_research_queue_status ON research_queue(status);
CREATE INDEX IF NOT EXISTS idx_research_queue_created_at ON research_queue(created_at);
