import zipfile
import pathlib
import logging
import csv
import random
import os
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
        self.proxy_files = ['Free_Proxy_List.txt', 'Free_Proxy_List_2.txt']
        
        # Load proxy lists
        self.proxy_list = self.load_proxies()
        self.current_proxy_index = 0
        self.logger.info(f"Loaded {len(self.proxy_list)} proxies")

    @classmethod
    def from_crawler(cls, crawler):
        """Create instance from crawler"""
        middleware = cls()
        middleware.proxy_enabled = crawler.settings.getbool('PROXY_ROTATION_ENABLED', True)
        middleware.proxy_files = crawler.settings.getlist('PROXY_FILES', [
            'Free_Proxy_List.txt',
            'Free_Proxy_List_2.txt'
        ])
        return middleware
    
    def load_proxies(self):
        """Load proxies from CSV files"""
        proxy_list = []
        
        project_root = pathlib.Path(__file__).parent.parent
        
        for filename in self.proxy_files:
            filepath = project_root / filename
            if not filepath.exists():
                self.logger.warning(f"Proxy file not found: {filepath}")
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Extract proxy info
                        ip = row.get('ip', '').strip('"')
                        port = row.get('port', '').strip('"')
                        protocols = row.get('protocols', '').strip('"')
                        anonymity = row.get('anonymityLevel', '').strip('"')
                        
                        # Only use elite proxies
                        if anonymity == 'elite' and ip and port:
                            proxy_list.append({
                                'ip': ip,
                                'port': port,
                                'protocol': protocols,
                                'anonymity': anonymity,
                                'country': row.get('country', '').strip('"')
                            })
                
                self.logger.info(f"Loaded {len(proxy_list)} proxies from {filename}")
            except Exception as e:
                self.logger.error(f"Error loading proxies from {filename}: {e}")
        
        # Shuffle proxy list for better distribution
        random.shuffle(proxy_list)
        return proxy_list
    
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