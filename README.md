# Selenium Scraper with Scrapy

A web scraping project using Scrapy framework with Selenium integration for dynamic content scraping.

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Test Spider

```bash
# Test the environment
./test_environment.sh

# Or run spider directly
scrapy crawl final_test
```

Output will be saved to `final_test_output.json`.

### 3. View Results

```bash
# Pretty print JSON
cat final_test_output.json | python3 -m json.tool

# Count items
cat final_test_output.json | grep -o '"text":' | wc -l
```

## Project Structure

```
selenium-scraper/
├── testSpider/              # Main Scrapy project
│   ├── spiders/             # Spider modules
│   │   ├── final_test.py    # Example spider (quotes)
│   │   └── test.py          # Original spider
│   ├── settings.py          # Scrapy settings
│   └── custom_middleware.py # Custom Selenium middleware
├── venv/                    # Virtual environment (not in git)
├── requirements.txt         # Python dependencies
├── test_environment.sh      # Environment verification script
└── scrapy.cfg              # Scrapy configuration
```

## Available Spiders

### final_test (Example Spider)
Scrapes quotes from http://quotes.toscrape.com/

```bash
scrapy crawl final_test
```

**Features:**
- Uses Selenium for dynamic content
- Collects quotes, authors, and tags
- Auto-saves to JSON file
- Pagination support (limited to 2 pages for testing)

### test (Original Spider)
Original spider for scraping ndis.gov.au

```bash
scrapy crawl test
```

## Configuration

### Key Settings (testSpider/settings.py)

```python
DOWNLOAD_DELAY = 2                    # Request delay in seconds
RANDOMIZE_DOWNLOAD_DELAY = True       # Randomize delay
CONCURRENT_REQUESTS_PER_DOMAIN = 16   # Concurrent requests
COOKIES_ENABLED = False               # Disable cookies
```

### Custom Middleware

The project uses `SeleniumMiddleware` which:
- Integrates undetected-chromedriver to avoid detection
- Handles dynamic content loading
- Manages browser sessions automatically
- Supports user agent rotation
- **Proxy rotation** - Automatically rotates through proxy lists

#### Proxy Rotation

The middleware automatically loads and rotates proxies from:
- `Free_Proxy_List.txt` (AU proxies)
- `Free_Proxy_List_2.txt` (JP proxies)

Features:
- Loads all elite proxies from CSV files
- Automatically rotates to next proxy for each browser session
- Supports SOCKS4, SOCKS5, and HTTP protocols
- Shuffles proxy list for better distribution

The proxy will change when:
- Spider starts (first request)
- Browser session is reset (after max_requests_per_driver)

**Test Proxy Loading:**
```bash
python test_proxy_rotation.py
```

**Disable Proxy Rotation:**
Set in `testSpider/settings.py`:
```python
PROXY_ROTATION_ENABLED = False
```

**Proxy Statistics:**
- Total: 96 elite proxies
- Australia (AU): 28 proxies
- Japan (JP): 68 proxies
- Protocols: SOCKS4 (77), SOCKS5 (19)

## Creating Your Own Spider

```python
import scrapy
from scrapy_selenium import SeleniumRequest

class MySpider(scrapy.Spider):
    name = "myspider"
    
    def start_requests(self):
        yield SeleniumRequest(
            url="http://example.com",
            wait_time=3,
            callback=self.parse
        )
    
    def parse(self, response):
        # Extract data
        yield {
            'title': response.css('h1::text').get(),
            'url': response.url
        }
```

## Common Commands

```bash
# List all spiders
scrapy list

# Run spider with output file
scrapy crawl spider_name -o output.json

# Run with overwrite
scrapy crawl spider_name -O output.json

# Export as CSV
scrapy crawl spider_name -o output.csv

# Check settings
scrapy settings --get DOWNLOAD_DELAY
```

## Dependencies

Key packages:
- **Scrapy 2.11.2** - Web scraping framework
- **Selenium 4.22.0** - Browser automation
- **undetected-chromedriver 3.5.5** - Undetectable Chrome driver
- **BeautifulSoup4 4.12.3** - HTML parsing
- **pandas** - Data manipulation
- **lxml** - XML/HTML parser

See `requirements.txt` for complete list.

## Troubleshooting

### Chrome driver not found
The project uses undetected-chromedriver which auto-downloads the driver. Ensure Chrome browser is installed.

### Import errors
```bash
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Spider runs but no output
Check that your spider uses `yield` to return data, or manually saves data in the `close()` method.

## Test Websites

Good websites for testing scrapers:
- http://quotes.toscrape.com/ - Quotes website
- http://books.toscrape.com/ - Books catalog
- http://toscrape.com/ - Collection of test sites

## Environment Info

- **Python**: 3.13+
- **OS**: macOS / Linux / Windows
- **Browser**: Chrome (required for Selenium)

## Notes

- Virtual environment (`venv/`) is excluded from git
- Chrome browser will open during scraping (non-headless mode by default)
- Spiders have page limits for testing purposes
- Output files are saved in project root

## License

This is a test/educational project for web scraping demonstration.
