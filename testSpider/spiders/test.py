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
        
        # Keep clicking Load More until no more data
        while True:
            # Extract cards from current view
            cards_extracted = self.extract_cards(response, driver)
            self.logger.info(f"Extracted {cards_extracted} cards from current view")
            
            # Try to click Load More button
            if not self.click_load_more(driver):
                self.logger.info("No more Load More button - scraping complete")
                break
            
            # Wait for new content to load
            time.sleep(3)
            
            # Update response with new page source
            body = str.encode(driver.page_source)
            response = response.replace(body=body)
            
            self.load_more_clicks += 1
            self.logger.info(f"Clicked Load More {self.load_more_clicks} times")
        
        self.logger.info(f"Total cards scraped: {self.cards_scraped}")
    
    def extract_cards(self, response, driver):
        """Extract card data from current page"""
        count = 0
        
        # Find all card elements
        # Adjust selectors based on actual website structure
        card_elements = response.css('div.card-item, article.card, div[data-card]')
        
        if not card_elements:
            # Try alternative selectors
            card_elements = response.css('a[href*="/card/"], div.index-card')
        
        for card in card_elements:
            try:
                # Extract card name
                name = card.css('h3::text, .card-title::text, .card-name::text').get()
                if not name:
                    name = card.css('::text').get()
                
                # Extract tag (rarity/type)
                tag = card.css('.rarity::text, .card-type::text, .badge::text, span.tag::text').get()
                
                if name:
                    name = name.strip()
                    tag = tag.strip() if tag else ''
                    
                    item = {
                        'name': name,
                        'tag': tag
                    }
                    
                    self.cards_scraped += 1
                    count += 1
                    yield item
                    
            except Exception as e:
                self.logger.error(f"Error extracting card: {e}")
                continue
        
        return count
    
    def click_load_more(self, driver):
        """Click Load More button if available"""
        try:
            # Wait a bit for any animations
            time.sleep(1)
            
            # Try multiple possible selectors for Load More button
            selectors = [
                "//button[contains(text(), 'Load More')]",
                "//button[contains(text(), 'Load more')]",
                "//button[contains(text(), 'Show More')]",
                "//a[contains(text(), 'Load More')]",
                "//button[@class*='load-more']",
                "//button[@id*='load-more']",
                "//div[@class*='load-more']//button"
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
            
            # Click button
            button.click()
            self.logger.info("✓ Clicked Load More button")
            
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
