import json
import scrapy
from scrapy_selenium import SeleniumRequest


class FinalTestSpider(scrapy.Spider):
    name = "final_test"
    
    def __init__(self, *args, **kwargs):
        super(FinalTestSpider, self).__init__(*args, **kwargs)
        # Using a simple test website that works well with Selenium
        self.start_urls = ["http://quotes.toscrape.com/"]
        self.collected_items = []
        self.max_pages = 2  # Limit for testing

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(url=url, wait_time=3, callback=self.parse)

    def parse(self, response):
        # Extract quotes
        quotes = response.css('div.quote')
        
        for quote in quotes:
            text = quote.css('span.text::text').get()
            author = quote.css('small.author::text').get()
            tags = quote.css('div.tags a.tag::text').getall()
            
            item = {
                'text': text,
                'author': author,
                'tags': tags,
                'url': response.url
            }
            
            self.collected_items.append(item)
        
        print(f"✓ Processed: {response.url}")
        print(f"  Found {len(quotes)} quotes on this page")
        
        # Follow pagination (limit for testing)
        if len(self.collected_items) < self.max_pages * 10:
            next_page = response.css('li.next a::attr(href)').get()
            if next_page:
                next_url = response.urljoin(next_page)
                yield SeleniumRequest(url=next_url, wait_time=3, callback=self.parse)

    def close(self, reason):
        output_file = 'final_test_output.json'
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(self.collected_items, file, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Spider closed: {reason}")
        print(f"Total items collected: {len(self.collected_items)}")
        print(f"Output saved to: {output_file}")
        print(f"{'='*60}\n")


# Run command: scrapy crawl final_test

