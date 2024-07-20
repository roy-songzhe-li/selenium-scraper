import os
import json
import scrapy
from bs4 import BeautifulSoup
from scrapy_selenium import SeleniumRequest
from urllib.parse import urljoin

class TestSpider(scrapy.Spider):
    name = "test"

    def __init__(self, *args, **kwargs):
        super(TestSpider, self).__init__(*args, **kwargs)
        self.start_urls = ["https://www.ndis.gov.au/"]
        self.keyword = "ndis"
        self.allowed_domains = [
            url.split("//")[-1].split("/")[0] for url in self.start_urls
        ]
        self.output_filename = f"{self.allowed_domains[0].replace('.', '_')}.json"
        self.unique_urls = []
        self.collected_items = []

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(url=url, wait_time=10, callback=self.parse)

    def parse(self, response):
        page_data = response.css("body").get()
        soup = BeautifulSoup(page_data, "lxml")
        text = " ".join(soup.get_text().split())

        item = {
            'sub_url': response.url,
            'html': response.text,
            'text': text
        }
        self.collected_items.append(item)
        print(f"Processed page: {response.url}")

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if full_url not in self.unique_urls and self.keyword in full_url:
                self.unique_urls.append(full_url)
                yield SeleniumRequest(url=full_url, wait_time=10, callback=self.parse)

    def close(self, reason):
        with open(self.output_filename, 'w', encoding='utf-8') as file:
            json.dump(self.collected_items, file, ensure_ascii=False, indent=4)

# to run the scraper：scrapy crawl test