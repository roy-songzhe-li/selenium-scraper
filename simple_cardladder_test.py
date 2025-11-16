#!/usr/bin/env python3
"""
Simple test to check CardLadder website structure
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

print("启动浏览器...")
options = uc.ChromeOptions()
driver = uc.Chrome(options=options, headless=False, use_subprocess=False)

try:
    print("访问 CardLadder...")
    driver.get('https://www.cardladder.com/indexes/pokemon')
    
    print(f"等待页面加载...")
    time.sleep(10)
    
    print(f"\n页面标题: {driver.title}")
    print(f"当前 URL: {driver.current_url}\n")
    
    # Check for Cloudflare
    if "just a moment" in driver.title.lower():
        print("⚠️  检测到 Cloudflare 保护，继续等待...")
        time.sleep(15)
        print(f"新标题: {driver.title}")
    
    # Save page source
    with open('cardladder_page.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("✅ 页面源码已保存到 cardladder_page.html\n")
    
    # Try to find cards
    print("查找卡片元素...")
    
    # Try different selectors
    selectors = [
        ('a[href*="/card/"]', 'Links containing /card/'),
        ('div[class*="card"]', 'Divs with card in class'),
        ('article', 'Article elements'),
        ('li[class*="item"]', 'List items'),
    ]
    
    for selector, desc in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        print(f"  {desc}: {len(elements)} 个元素")
        
        if elements and len(elements) > 0:
            print(f"    示例: {elements[0].text[:100] if elements[0].text else '(no text)'}")
    
    # Find all buttons
    print("\n查找按钮...")
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    print(f"  找到 {len(buttons)} 个按钮")
    
    for btn in buttons[:10]:
        text = btn.text
        if text:
            print(f"    - \"{text}\" | class=\"{btn.get_attribute('class')}\"")
    
    input("\n按 Enter 关闭浏览器...")
    
finally:
    driver.quit()
    print("浏览器已关闭")

