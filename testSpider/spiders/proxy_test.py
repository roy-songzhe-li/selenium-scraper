import json
import scrapy
from scrapy_selenium import SeleniumRequest


class ProxyTestSpider(scrapy.Spider):
    """Test spider to verify proxy is working"""
    name = "proxy_test"
    
    def __init__(self, *args, **kwargs):
        super(ProxyTestSpider, self).__init__(*args, **kwargs)
        # Use a simple IP checking website
        self.start_urls = ["http://httpbin.org/ip"]
        self.collected_items = []

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(url=url, wait_time=10, callback=self.parse)

    def parse(self, response):
        # Try to extract the IP that the website sees
        text = response.css('body::text').get()
        
        item = {
            'url': response.url,
            'body': text,
            'proxy_used': 'Check middleware logs for proxy info'
        }
        
        self.collected_items.append(item)
        
        print(f"\n{'='*60}")
        print(f"Response from {response.url}:")
        print(f"Body: {text[:200] if text else 'No text'}")
        print(f"{'='*60}\n")

    def close(self, reason):
        output_file = 'proxy_test_output.json'
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(self.collected_items, file, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Proxy Test Spider Closed: {reason}")
        print(f"Output saved to: {output_file}")
        print(f"Check the logs above to see which proxy was used")
        print(f"{'='*60}\n")


# Run command: scrapy crawl proxy_test
# Look for log line: "INFO: Using proxy: <ip>:<port>"

