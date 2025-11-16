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
        self.logger.info("🕷️  Starting card extraction...")
        
        # Keep clicking Load More until no more data
        while True:
            # Extract cards from current view
            cards_extracted = list(self.extract_cards(response, driver))
            count = len(cards_extracted)
            
            # Yield extracted items
            for item in cards_extracted:
                yield item
            
            if count > 0:
                self.logger.info(f"✓ Batch: {count} cards | Total: {self.cards_scraped} | Load More clicks: {self.load_more_clicks}")
            else:
                self.logger.info(f"⚠️  No new cards found in this batch")
            
            # Try to click Load More button
            load_more_result = self.click_load_more(driver)
            if not load_more_result:
                self.logger.info("🏁 No more Load More button - scraping complete!")
                break
            
            self.load_more_clicks += 1
            self.logger.info(f"⏳ Loading more cards... (click #{self.load_more_clicks})")
            
            # Wait for new content to load  
            time.sleep(0.8)
            
            # Update response with new page source
            body = str.encode(driver.page_source)
            response = response.replace(body=body)
        
        self.logger.info(f"Total cards scraped: {self.cards_scraped}")
    
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
                
                # Extract tag (rarity)
                tag = card.css('span.grade-variation-chip span:first-child::text').get()
                
                # Build full card name
                if card_set and name_text:
                    card_set = card_set.strip()
                    name_text = name_text.strip()
                    number_text = number_text.strip() if number_text else ''
                    
                    # Full name: "2021 Pokemon Sword & Shield: Fusion Strike Espeon VMAX #270"
                    full_name = f"{card_set} {name_text} {number_text}".strip()
                    
                    # Clean tag
                    tag = tag.strip() if tag else ''
                    
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
            time.sleep(0.3)
            
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
            time.sleep(0.2)
            
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
