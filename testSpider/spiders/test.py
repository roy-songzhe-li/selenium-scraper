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
        self.start_urls = ["https://liushilive.github.io/pages/"]
        self.allowed_domains = [
            url.split("//")[-1].split("/")[0] for url in self.start_urls
        ]
        self.unique_urls = []
        self.collected_items = []  # 收集所有条目的列表

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(url=url, wait_time=10, callback=self.parse)

    def parse(self, response):
        # 确保从当前响应中提取数据
        page_data = response.css("body").get()
        soup = BeautifulSoup(page_data, "lxml")
        text = " ".join(soup.get_text().split())

        item = {
            'sub_url': response.url,
            'html': response.text,  # 使用 response.text 获取当前页面的 HTML 源码
            'text': text
        }
        self.collected_items.append(item)
        print(f"Processed page: {response.url}")

        # 追踪链接并发起新的请求
        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if full_url not in self.unique_urls:
                self.unique_urls.append(full_url)
                yield SeleniumRequest(url=full_url, wait_time=10, callback=self.parse)

    def close(self, reason):
        # 爬虫关闭时写入 JSON 文件
        with open('results.json', 'w', encoding='utf-8') as file:
            json.dump(self.collected_items, file, ensure_ascii=False, indent=4)

# 运行爬虫命令：scrapy crawl test
