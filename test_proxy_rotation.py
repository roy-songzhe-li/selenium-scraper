#!/usr/bin/env python3
"""
Test script for proxy rotation functionality
"""
import sys
import pathlib

# Add project to path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from testSpider.custom_middleware import SeleniumMiddleware


def test_proxy_loading():
    """Test proxy loading from CSV files"""
    print("=" * 60)
    print("Testing Proxy Loading and Rotation")
    print("=" * 60)
    
    # Create middleware instance
    middleware = SeleniumMiddleware()
    
    # Check if proxies loaded
    print(f"\nTotal proxies loaded: {len(middleware.proxy_list)}")
    
    if not middleware.proxy_list:
        print("❌ No proxies loaded! Check if CSV files exist.")
        return False
    
    # Show first 5 proxies
    print("\nFirst 5 proxies:")
    for i, proxy in enumerate(middleware.proxy_list[:5], 1):
        print(f"  {i}. {proxy['ip']}:{proxy['port']} - {proxy['protocol']} ({proxy['country']})")
    
    # Test rotation
    print("\n" + "=" * 60)
    print("Testing Proxy Rotation (Next 10 proxies)")
    print("=" * 60)
    
    for i in range(10):
        proxy = middleware.get_next_proxy()
        if proxy:
            print(f"  Request {i+1}: {proxy['ip']}:{proxy['port']} - {proxy['protocol']} ({proxy['country']})")
        else:
            print(f"  Request {i+1}: No proxy returned")
    
    # Test statistics
    print("\n" + "=" * 60)
    print("Proxy Statistics")
    print("=" * 60)
    
    # Count by country
    countries = {}
    for proxy in middleware.proxy_list:
        country = proxy.get('country', 'Unknown')
        countries[country] = countries.get(country, 0) + 1
    
    print("\nProxies by country:")
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
        print(f"  {country}: {count}")
    
    # Count by protocol
    protocols = {}
    for proxy in middleware.proxy_list:
        protocol = proxy.get('protocol', 'Unknown')
        protocols[protocol] = protocols.get(protocol, 0) + 1
    
    print("\nProxies by protocol:")
    for protocol, count in sorted(protocols.items(), key=lambda x: x[1], reverse=True):
        print(f"  {protocol}: {count}")
    
    print("\n" + "=" * 60)
    print("✅ Proxy loading and rotation test completed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_proxy_loading()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

