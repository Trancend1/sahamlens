-- Migration 0002 — extend `news` table with summary metadata fields.
-- Adds: source_quality, confidence, caveats (JSON), prompt_template_id, model, summarized_at.
-- `summarized_at IS NULL` drives batch backlog for the summarizer.

ALTER TABLE news ADD COLUMN IF NOT EXISTS source_quality TEXT;
ALTER TABLE news ADD COLUMN IF NOT EXISTS confidence REAL;
ALTER TABLE news ADD COLUMN IF NOT EXISTS caveats TEXT;
ALTER TABLE news ADD COLUMN IF NOT EXISTS prompt_template_id TEXT;
ALTER TABLE news ADD COLUMN IF NOT EXISTS model TEXT;
ALTER TABLE news ADD COLUMN IF NOT EXISTS summarized_at TEXT;

CREATE INDEX IF NOT EXISTS idx_news_published_at ON news(published_at);
CREATE INDEX IF NOT EXISTS idx_news_summarized_at ON news(summarized_at);
