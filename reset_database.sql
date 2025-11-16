-- Complete database reset with ID sequence restart
-- Run this in Supabase SQL Editor

-- Delete all records and reset ID sequence to start from 1
TRUNCATE TABLE cards RESTART IDENTITY CASCADE;

-- Verify
SELECT COUNT(*) as record_count FROM cards;
SELECT last_value FROM cards_id_seq;

