import os
import json
import time
import scrapy
from bs4 import BeautifulSoup
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestSpider(scrapy.Spider):
    name = "test"
    
    def __init__(self, *args, **kwargs):
        super(TestSpider, self).__init__(*args, **kwargs)
        # CardLadder Pokemon index page
        self.start_urls = ["https://www.cardladder.com/indexes/pokemon"]
        self.cards_scraped = 0
        self.load_more_clicks = 0

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                wait_time=5,
                callback=self.parse,
                dont_filter=True
            )

    def parse(self, response):
        """Parse card data and handle Load More button"""
        driver = response.meta.get('driver')
        
        if not driver:
            self.logger.error("No driver found in response meta")
            return
        
        # Check for Cloudflare
        if "just a moment" in driver.title.lower():
            self.logger.info("⏳ Waiting for Cloudflare bypass...")
            time.sleep(8)
        
        self.logger.info(f"✓ Page loaded: {driver.title}")
        self.logger.info(f"✓ URL: {driver.current_url}")
        
        # Step 1: Click all Load More buttons first
        self.logger.info("🔄 Loading all cards (clicking Load More repeatedly)...")
        
        # Track card count to detect when no more cards are being added
        prev_card_count = 0
        no_change_count = 0
        
        while True:
            # Count current cards
            current_cards = driver.find_elements(By.CSS_SELECTOR, 'div.card-item-info')
            current_count = len(current_cards)
            
            # Check if card count stopped increasing
            if current_count == prev_card_count:
                no_change_count += 1
                if no_change_count >= 3:
                    self.logger.info(f"⚠️  Card count unchanged for 3 clicks - stopping")
                    self.logger.info(f"✓ Final card count on page: {current_count}")
                    break
            else:
                no_change_count = 0
            
            # Try to click Load More button
            if not self.click_load_more(driver):
                self.logger.info(f"✓ All cards loaded! (clicked {self.load_more_clicks} times)")
                break
            
            self.load_more_clicks += 1
            prev_card_count = current_count
            
            if self.load_more_clicks % 10 == 0:
                self.logger.info(f"⏳ Clicked {self.load_more_clicks} times | Cards on page: {current_count}")
            
            # Wait for new content to load
            time.sleep(2)
        
        # Step 2: Now extract all cards at once
        self.logger.info(f"🕷️  Extracting all {self.load_more_clicks * 20}+ cards...")
        
        # Update response with final page source
        body = str.encode(driver.page_source)
        response = response.replace(body=body)
        
        # Extract all cards
        cards_extracted = list(self.extract_cards(response, driver))
        
        # Yield all items
        for item in cards_extracted:
            yield item
        
        self.logger.info(f"✅ Extraction complete!")
        self.logger.info(f"📊 Total unique cards: {len(cards_extracted)}")
    
    def extract_cards(self, response, driver):
        """Extract card data from current page using correct selectors"""
        # Find all card items using the actual class structure
        card_items = response.css('div.card-item-info')
        
        if not card_items:
            self.logger.warning("⚠️  No card-item-info elements found")
            return
        
        for card in card_items:
            try:
                # Extract card set (year + set name)
                card_set = card.css('div.card-set::text').get()
                
                # Extract card name and number
                card_name_elem = card.css('div.card-name')
                name_text = card_name_elem.css('span:first-child::text').get()
                number_text = card_name_elem.css('span:last-child::text').get()
                
                # Extract ALL chips (rarity + grade)
                chips = card.css('span.grade-variation-chip span:first-child::text').getall()
                # Combine all chips into tag (e.g., "Holo PSA 10" or "Full Art Secret Rare CGC 9.5")
                tag = ' '.join([c.strip() for c in chips if c.strip()])
                
                # Build full card name
                if card_set and name_text:
                    card_set = card_set.strip()
                    name_text = name_text.strip()
                    number_text = number_text.strip() if number_text else ''
                    
                    # Full name: "2021 Pokemon Sword & Shield: Fusion Strike Espeon VMAX #270"
                    full_name = f"{card_set} {name_text} {number_text}".strip()
                    
                    # Don't skip duplicates - extract ALL cards
                    # Database will handle uniqueness with upsert
                    item = {
                        'name': full_name,
                        'tag': tag
                    }
                    
                    self.cards_scraped += 1
                    yield item
                    
            except Exception as e:
                self.logger.error(f"❌ Error extracting card: {e}")
                continue
    
    def click_load_more(self, driver):
        """Click Load More button if available"""
        try:
            # Wait a bit for any animations
            time.sleep(0.5)
            
            # Try multiple possible selectors for Load More button
            selectors = [
                "//button[contains(@class, 'btn') and contains(@class, 'secondary') and contains(text(), 'Load more')]",
                "//button[contains(text(), 'Load more')]",
                "//button[contains(text(), 'Load More')]",
                "//button[@class='btn secondary']"
            ]
            
            button = None
            for selector in selectors:
                try:
                    button = driver.find_element(By.XPATH, selector)
                    if button and button.is_displayed() and button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if not button:
                return False
            
            # Check if button is disabled
            if not button.is_enabled():
                self.logger.info("Load More button is disabled")
                return False
            
            # Scroll to button
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(0.5)
            
            # Try JavaScript click if regular click fails
            try:
                button.click()
            except:
                driver.execute_script("arguments[0].click();", button)
            
            return True
            
        except TimeoutException:
            self.logger.info("Load More button not found (timeout)")
            return False
        except Exception as e:
            self.logger.error(f"Error clicking Load More: {e}")
            return False
    
    def close(self, reason):
        """Log final statistics"""
        self.logger.info("=" * 60)
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Total cards scraped: {self.cards_scraped}")
        self.logger.info(f"Load More clicks: {self.load_more_clicks}")
        self.logger.info("=" * 60)


# Run command: scrapy crawl test
