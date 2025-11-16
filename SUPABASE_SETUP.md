# Supabase + CardLadder Setup Guide

## Step 1: Create Database Table

1. Visit Supabase Dashboard: https://dmsvsfsbytemtbbqxqyi.supabase.co
2. Go to **SQL Editor**
3. Copy and paste the contents of `create_tables.sql`
4. Click **Run** to create the table

## Step 2: Test Connection

```bash
./venv/bin/python test_supabase_connection.py
```

Expected output:
```
✅ Successfully created Supabase client
✅ Connected to cards table
✅ Test insert successful
```

## Step 3: Run Scraper

```bash
./venv/bin/scrapy crawl test
```

The scraper will:
- Navigate to https://www.cardladder.com/indexes/pokemon
- Automatically click "Load More" until all cards are loaded
- Extract card names and tags
- Save directly to Supabase database
- Use proxy rotation automatically (159 proxies)

## Monitoring

Watch the logs for:
- `✓ Clicked Load More button` - Progress indicator
- `✓ Inserted: <card name>` - Database insertions
- `Using proxy: <ip>:<port>` - Proxy rotation
- `Total cards scraped: X` - Final count

## Database Structure

**Table:** `cards`

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Primary key |
| name | TEXT | Card name (e.g., "2003 Pokemon Skyridge Charizard #146") |
| tag | TEXT | Rarity/type (e.g., "Secret Rare", "Holo Gold Star") |
| created_at | TIMESTAMP | Auto-generated |
| updated_at | TIMESTAMP | Auto-generated |

**Unique constraint:** `name` (prevents duplicates)

## Configuration Files

- `.env` - Supabase credentials (not in git)
- `testSpider/settings.py` - Pipeline enabled
- `testSpider/supabase_pipeline.py` - Database insertion logic
- `testSpider/spiders/test.py` - CardLadder scraper

## Disable Proxy (Optional)

In `testSpider/settings.py`:
```python
PROXY_ROTATION_ENABLED = False
```

## View Data in Supabase

1. Go to Supabase Dashboard
2. Click **Table Editor**
3. Select **cards** table
4. View all scraped Pokemon cards

