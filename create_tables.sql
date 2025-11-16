-- Create cards table for Pokemon TCG data
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS cards (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tag TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name)
);

-- Create index on name for faster lookups
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);

-- Create index on tag for filtering
CREATE INDEX IF NOT EXISTS idx_cards_tag ON cards(tag);

-- Add comment
COMMENT ON TABLE cards IS 'Pokemon TCG cards scraped from cardladder.com';
COMMENT ON COLUMN cards.name IS 'Full card name including year, set, and number (e.g., 2003 Pokemon Skyridge Charizard #146)';
COMMENT ON COLUMN cards.tag IS 'Card rarity/type tag (e.g., Secret Rare, Holo Gold Star)';

