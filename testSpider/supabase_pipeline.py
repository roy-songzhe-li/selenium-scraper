"""
Supabase Pipeline for storing scraped Pokemon cards
"""
import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabasePipeline:
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase = None
        self.inserted_count = 0
        self.duplicate_count = 0
        self.error_count = 0
    
    def open_spider(self, spider):
        """Initialize Supabase connection when spider opens"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.error("Supabase credentials not found in environment variables")
                raise ValueError("Missing Supabase credentials")
            
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self.logger.info("Successfully connected to Supabase")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Supabase: {e}")
            raise
    
    def process_item(self, item, spider):
        """Process and insert item into Supabase"""
        try:
            # Extract data
            name = item.get('name', '').strip()
            tag = item.get('tag', '').strip()
            
            if not name:
                self.logger.warning("Skipping item without name")
                return item
            
            # Prepare data
            card_data = {
                'name': name,
                'tag': tag if tag else None
            }
            
            # Insert into Supabase (upsert to handle duplicates based on name+tag)
            response = self.supabase.table('cards').upsert(
                card_data,
                on_conflict='name,tag'
            ).execute()
            
            if response.data:
                self.inserted_count += 1
                if self.inserted_count % 20 == 0:
                    self.logger.info(f"💾 Saved {self.inserted_count} cards to database")
            else:
                self.duplicate_count += 1
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error inserting item {item.get('name', 'unknown')}: {e}")
        
        return item
    
    def close_spider(self, spider):
        """Log statistics when spider closes"""
        self.logger.info("=" * 60)
        self.logger.info("Supabase Pipeline Statistics")
        self.logger.info("=" * 60)
        self.logger.info(f"Inserted: {self.inserted_count}")
        self.logger.info(f"Duplicates: {self.duplicate_count}")
        self.logger.info(f"Errors: {self.error_count}")
        self.logger.info(f"Total processed: {self.inserted_count + self.duplicate_count + self.error_count}")
        self.logger.info("=" * 60)

