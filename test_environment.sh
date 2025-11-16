#!/bin/bash

# Test Environment Script for Selenium Scraper
# This script verifies that the environment is properly configured

echo "=========================================="
echo "Testing Selenium Scraper Environment"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: python3 -m venv venv"
    exit 1
else
    echo "✓ Virtual environment found"
fi

# Activate virtual environment
source venv/bin/activate

# Check Python version
echo ""
echo "Python version:"
python --version

# Check if scrapy is installed
echo ""
if command -v scrapy &> /dev/null; then
    echo "✓ Scrapy is installed"
    scrapy version
else
    echo "❌ Scrapy is not installed"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

# Check if key packages are installed
echo ""
echo "Checking key packages:"
python -c "import selenium; print('✓ Selenium version:', selenium.__version__)"
python -c "import scrapy; print('✓ Scrapy version:', scrapy.__version__)"
python -c "import undetected_chromedriver; print('✓ Undetected ChromeDriver installed')"
python -c "import bs4; print('✓ BeautifulSoup4 installed')"
python -c "import pandas; print('✓ Pandas installed')"

# List available spiders
echo ""
echo "Available spiders:"
scrapy list

# Run test spider
echo ""
echo "=========================================="
echo "Running test spider (final_test)..."
echo "=========================================="
scrapy crawl final_test

# Check if output file was created
echo ""
if [ -f "final_test_output.json" ]; then
    echo "✓ Output file created successfully"
    echo ""
    echo "Sample output (first 10 lines):"
    head -10 final_test_output.json
    echo ""
    ITEM_COUNT=$(cat final_test_output.json | grep -o '"text":' | wc -l)
    echo "✓ Total items collected: $ITEM_COUNT"
else
    echo "❌ Output file not created"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ Environment test completed successfully!"
echo "=========================================="
echo ""
echo "Your Selenium Scraper environment is ready to use."
echo ""
echo "Available test spiders:"
echo "  - scrapy crawl final_test    (Quotes scraper)"
echo "  - scrapy crawl books_test    (Books scraper)"
echo "  - scrapy crawl simple_test   (Simple static scraper)"
echo ""

