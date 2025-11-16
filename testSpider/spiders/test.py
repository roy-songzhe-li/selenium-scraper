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
                wait_time=10,
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
            time.sleep(5)
        
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
            time.sleep(1.5)
            
            # Update response with new page source
            body = str.encode(driver.page_source)
            response = response.replace(body=body)
        
        self.logger.info(f"Total cards scraped: {self.cards_scraped}")
    
    def extract_cards(self, response, driver):
        """Extract card data from current page"""
        # Find all card links
        card_links = response.css('a[href*="/card/"]')
        
        for card_link in card_links:
            try:
                # Get full text content from link
                text = card_link.css('::text').getall()
                full_text = ' '.join([t.strip() for t in text if t.strip()])
                
                if not full_text:
                    continue
                
                # Parse card name and tag
                # Format: "2003 Pokemon Skyridge Charizard #146 Secret Rare ..."
                parts = full_text.split()
                
                # Find where the tag starts (usually after card number #XXX)
                name_parts = []
                tag_parts = []
                found_number = False
                collecting_tag = False
                
                for i, part in enumerate(parts):
                    if '#' in part:
                        name_parts.append(part)
                        found_number = True
                        # Next significant words are likely the tag
                        continue
                    
                    if found_number and not collecting_tag:
                        # Check if this looks like a tag (Secret, Rare, Holo, etc.)
                        tag_keywords = ['Secret', 'Rare', 'Holo', 'Gold', 'Star', 'PSA']
                        if any(keyword.lower() in part.lower() for keyword in tag_keywords):
                            collecting_tag = True
                            tag_parts.append(part)
                        elif not part.replace(',', '').isdigit() and part.lower() not in ['no', 'results', 'pop']:
                            tag_parts.append(part)
                    elif collecting_tag:
                        # Continue collecting tag until we hit PSA or numbers
                        if 'PSA' in part or part.isdigit():
                            break
                        if part.lower() not in ['no', 'results']:
                            tag_parts.append(part)
                    else:
                        name_parts.append(part)
                
                name = ' '.join(name_parts).strip()
                tag = ' '.join(tag_parts).strip() if tag_parts else ''
                
                # Clean up common noise words
                for noise in ['No results', 'No result', 'PSA 10', 'PSA 9', 'Pop']:
                    name = name.replace(noise, '').strip()
                    tag = tag.replace(noise, '').strip()
                
                if name and len(name) > 10:  # Basic validation
                    item = {
                        'name': name,
                        'tag': tag
                    }
                    
                    self.cards_scraped += 1
                    yield item
                    
            except Exception as e:
                self.logger.error(f"Error extracting card: {e}")
                continue
    
    def click_load_more(self, driver):
        """Click Load More button if available"""
        try:
            # Wait a bit for any animations
            time.sleep(1)
            
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
            time.sleep(0.3)
            
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
