import zipfile
import pathlib
import logging
import csv
import random
import os
import requests
import undetected_chromedriver as uc
from scrapy.http import HtmlResponse
from fake_useragent import UserAgent
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumMiddleware(object):
    
    def __init__(self, max_requests_per_driver=1000000):
        self.driver = None
        self.request_count = 0
        self.max_requests_per_driver = max_requests_per_driver
        self.logger = logging.getLogger(__name__)
        
        # Default settings (will be overridden by from_crawler)
        self.proxy_enabled = True
        self.proxy_api_urls = [
            'https://proxylist.geonode.com/api/proxy-list?country=JP&limit=500&page=1&sort_by=lastChecked&sort_type=desc',
            'https://proxylist.geonode.com/api/proxy-list?country=AU&limit=500&page=1&sort_by=lastChecked&sort_type=desc',
        ]
        
        # Load proxy lists
        self.proxy_list = self.load_proxies()
        self.current_proxy_index = 0
        self.logger.info(f"Loaded {len(self.proxy_list)} proxies")

    @classmethod
    def from_crawler(cls, crawler):
        """Create instance from crawler"""
        middleware = cls()
        middleware.proxy_enabled = crawler.settings.getbool('PROXY_ROTATION_ENABLED', True)
        middleware.proxy_api_urls = crawler.settings.getlist('PROXY_API_URLS', [
            'https://proxylist.geonode.com/api/proxy-list?country=JP&limit=500&page=1&sort_by=lastChecked&sort_type=desc',
            'https://proxylist.geonode.com/api/proxy-list?country=AU&limit=500&page=1&sort_by=lastChecked&sort_type=desc',
        ])
        return middleware
    
    def load_proxies(self):
        """Load proxies from Geonode API"""
        proxy_list = []
        
        for api_url in self.proxy_api_urls:
            try:
                self.logger.info(f"Fetching proxies from API: {api_url}")
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                proxies = data.get('data', [])
                
                for proxy_data in proxies:
                    # Extract proxy info
                    ip = proxy_data.get('ip', '')
                    port = proxy_data.get('port', '')
                    protocols = proxy_data.get('protocols', [])
                    anonymity = proxy_data.get('anonymityLevel', '')
                    country = proxy_data.get('country', '')
                    
                    # Only use elite proxies
                    if anonymity == 'elite' and ip and port:
                        # Use first protocol from list
                        protocol = protocols[0] if protocols else 'socks5'
                        
                        proxy_list.append({
                            'ip': ip,
                            'port': str(port),
                            'protocol': protocol,
                            'anonymity': anonymity,
                            'country': country
                        })
                
                self.logger.info(f"Loaded {len(proxies)} proxies from {country} ({len([p for p in proxies if p.get('anonymityLevel') == 'elite'])} elite)")
                
            except Exception as e:
                self.logger.error(f"Error fetching proxies from API: {e}")
        
        # Remove duplicates based on ip:port
        seen = set()
        unique_proxies = []
        for proxy in proxy_list:
            key = f"{proxy['ip']}:{proxy['port']}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        # Shuffle proxy list for better distribution
        random.shuffle(unique_proxies)
        
        self.logger.info(f"Total unique elite proxies loaded: {len(unique_proxies)}")
        return unique_proxies
    
    def get_next_proxy(self):
        """Get next proxy from the list (rotation)"""
        if not self.proxy_enabled:
            return None
            
        if not self.proxy_list:
            self.logger.warning("No proxies available")
            return None
        
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        
        self.logger.info(f"Using proxy: {proxy['ip']}:{proxy['port']} ({proxy['protocol']}) - {proxy['country']}")
        return proxy

    def spider_closed(self, spider):
        if self.driver:
            self.driver.quit()

    def process_request(self, request, spider):
        self.logger.debug(f"Processing request: {request.url}")

        if not self.driver or self.request_count >= self.max_requests_per_driver:
            self.logger.debug("Initializing new driver")
            self.init_driver()
            self.request_count = 0

        if not isinstance(request, SeleniumRequest):
            self.logger.debug("Request is not a SeleniumRequest")
            return None

        try:
            self.logger.debug(f"Getting URL: {request.url}")
            self.driver.get(request.url)
            self.logger.debug(f"Page title: {self.driver.title}")

            if request.wait_until:
                WebDriverWait(self.driver, request.wait_time).until(
                    request.wait_until
                )

            if request.script:
                self.driver.execute_script(request.script)

            body = str.encode(self.driver.page_source)
            self.request_count += 1
            request.meta.update({'driver': self.driver})
            self.logger.debug(f"Processed request successfully: {request.url}")
            return HtmlResponse(self.driver.current_url, body=body, encoding='utf-8', request=request)

        except Exception as e:
            self.logger.error(f"Error processing request {request.url}: {e}")
            pass

    def getPlugin(self, proxy_host, proxy_port, proxy_user, proxy_pass):
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """
        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (proxy_host, proxy_port, proxy_user, proxy_pass)
        pluginfile = 'scraper\\userdata\\proxy_auth_plugin.zip'
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        return pluginfile

    def driver_return(self):
        options = uc.ChromeOptions()
        ua = UserAgent(browsers=['chrome'])
        options.add_argument("--window-size=150,500")
        options.add_argument("--disable-automation")
        options.add_argument("--no-sandbox")
        options.add_argument('--profile-directory=Default')
        options.add_argument("--lang=en")
        options.add_argument("--enable-javascript")
        options.add_argument("--enable-cookies")
        options.add_argument(f'--user-agent={ua.random}')
        
        # Add proxy configuration
        proxy = self.get_next_proxy()
        if proxy:
            protocol = proxy['protocol']
            ip = proxy['ip']
            port = proxy['port']
            
            # Configure proxy based on protocol
            if 'socks5' in protocol.lower():
                proxy_server = f"socks5://{ip}:{port}"
            elif 'socks4' in protocol.lower():
                proxy_server = f"socks4://{ip}:{port}"
            elif 'http' in protocol.lower():
                proxy_server = f"http://{ip}:{port}"
            else:
                # Default to socks5 if protocol not clear
                proxy_server = f"socks5://{ip}:{port}"
            
            options.add_argument(f'--proxy-server={proxy_server}')
            self.logger.info(f"Configured proxy: {proxy_server}")
        else:
            self.logger.warning("No proxy configured - running without proxy")
        
        prefs = {
            "download_restrictions": 3,
        }
        options.add_experimental_option(
            "prefs", prefs
        )
        
        scriptDirectory = pathlib.Path().absolute()
        # options.add_argument(f"--user-data-dir={scriptDirectory}\\testSpider\\userdata")
        driver = uc.Chrome(options=options, headless=False, use_subprocess=False)
        return driver

    def init_driver(self):
        if self.driver:
            self.driver.quit()
        self.driver = self.driver_return()
        self.driver.maximize_window()