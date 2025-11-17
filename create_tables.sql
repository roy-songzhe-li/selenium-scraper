-- Drop existing table and recreate
DROP TABLE IF EXISTS cards CASCADE;

-- Create cards table
-- Note: Removed UNIQUE constraint on name to allow same card with different grades
-- Each card+grade combination is a separate record
CREATE TABLE cards (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tag TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, tag)  -- Unique constraint on name+tag combination
);

-- Create index on name for faster lookups
CREATE INDEX idx_cards_name ON cards(name);

-- Create index on tag for filtering
CREATE INDEX idx_cards_tag ON cards(tag);

-- Add comment
COMMENT ON TABLE cards IS 'Pokemon TCG cards scraped from cardladder.com';
COMMENT ON COLUMN cards.name IS 'Full card name including year, set, and number';
COMMENT ON COLUMN cards.tag IS 'Card rarity/type tag';

