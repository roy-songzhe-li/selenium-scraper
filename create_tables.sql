-- Drop existing table and recreate
DROP TABLE IF EXISTS cards CASCADE;

-- Create cards table
-- Note: BIGSERIAL IDs may have gaps due to:
-- 1. Failed insert attempts (ID consumed but row not created)
-- 2. Concurrent transactions
-- 3. UPSERT operations (ID generated then discarded if duplicate found)
-- This is normal PostgreSQL behavior
CREATE TABLE cards (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    tag TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on name for faster lookups
CREATE INDEX idx_cards_name ON cards(name);

-- Create index on tag for filtering
CREATE INDEX idx_cards_tag ON cards(tag);

-- Add comment
COMMENT ON TABLE cards IS 'Pokemon TCG cards scraped from cardladder.com';
COMMENT ON COLUMN cards.name IS 'Full card name including year, set, and number';
COMMENT ON COLUMN cards.tag IS 'Card rarity/type tag';

