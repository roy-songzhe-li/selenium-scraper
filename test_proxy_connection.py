#!/usr/bin/env python3
"""
Test proxy connection quality
Tests actual connectivity of loaded proxies
"""
import sys
import pathlib
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from testSpider.custom_middleware import SeleniumMiddleware


def test_proxy_connection(proxy, timeout=10):
    """Test if a single proxy can connect"""
    ip = proxy['ip']
    port = proxy['port']
    protocol = proxy['protocol']
    country = proxy['country']
    
    # Build proxy URL
    if 'socks5' in protocol.lower():
        proxy_url = f"socks5://{ip}:{port}"
    elif 'socks4' in protocol.lower():
        proxy_url = f"socks4://{ip}:{port}"
    elif 'http' in protocol.lower():
        proxy_url = f"http://{ip}:{port}"
    else:
        proxy_url = f"socks5://{ip}:{port}"
    
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    try:
        # Test with a simple HTTP request
        start_time = time.time()
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxies,
            timeout=timeout
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            return {
                'proxy': f"{ip}:{port}",
                'protocol': protocol,
                'country': country,
                'status': 'OK',
                'response_time': round(elapsed, 2),
                'ip_seen': response.json().get('origin', 'N/A')
            }
    except requests.exceptions.ProxyError:
        return {'proxy': f"{ip}:{port}", 'status': 'PROXY_ERROR', 'country': country}
    except requests.exceptions.Timeout:
        return {'proxy': f"{ip}:{port}", 'status': 'TIMEOUT', 'country': country}
    except requests.exceptions.ConnectionError:
        return {'proxy': f"{ip}:{port}", 'status': 'CONNECTION_ERROR', 'country': country}
    except Exception as e:
        return {'proxy': f"{ip}:{port}", 'status': f'ERROR: {type(e).__name__}', 'country': country}
    
    return {'proxy': f"{ip}:{port}", 'status': 'FAILED', 'country': country}


def test_proxy_pool(max_proxies=20, workers=10):
    """Test a subset of proxies concurrently"""
    print("=" * 70)
    print("Testing Proxy Connection Quality")
    print("=" * 70)
    
    # Load proxies
    middleware = SeleniumMiddleware()
    
    if not middleware.proxy_list:
        print("❌ No proxies loaded!")
        return
    
    # Test subset
    test_count = min(max_proxies, len(middleware.proxy_list))
    proxies_to_test = middleware.proxy_list[:test_count]
    
    print(f"\nTesting {test_count} proxies out of {len(middleware.proxy_list)} total...")
    print(f"Using {workers} concurrent workers\n")
    
    working = []
    failed = []
    
    # Test proxies concurrently
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(test_proxy_connection, proxy): proxy 
            for proxy in proxies_to_test
        }
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            
            if result['status'] == 'OK':
                working.append(result)
                print(f"✅ [{i}/{test_count}] {result['proxy']} - {result['protocol']} ({result['country']}) - {result['response_time']}s")
            else:
                failed.append(result)
                print(f"❌ [{i}/{test_count}] {result['proxy']} ({result['country']}) - {result['status']}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"\n✅ Working proxies: {len(working)}/{test_count} ({len(working)/test_count*100:.1f}%)")
    print(f"❌ Failed proxies: {len(failed)}/{test_count} ({len(failed)/test_count*100:.1f}%)")
    
    if working:
        avg_time = sum(p['response_time'] for p in working) / len(working)
        print(f"\n📊 Average response time: {avg_time:.2f}s")
        print(f"⚡ Fastest proxy: {min(working, key=lambda x: x['response_time'])['proxy']} ({min(p['response_time'] for p in working):.2f}s)")
        print(f"🐌 Slowest proxy: {max(working, key=lambda x: x['response_time'])['proxy']} ({max(p['response_time'] for p in working):.2f}s)")
        
        print("\n🎯 Top 5 working proxies:")
        for i, proxy in enumerate(sorted(working, key=lambda x: x['response_time'])[:5], 1):
            print(f"  {i}. {proxy['proxy']} - {proxy['protocol']} ({proxy['country']}) - {proxy['response_time']}s")
    
    if failed:
        print("\n❌ Failure reasons:")
        error_types = {}
        for f in failed:
            status = f['status']
            error_types[status] = error_types.get(status, 0) + 1
        
        for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error}: {count}")
    
    print("\n" + "=" * 70)
    print("✅ Connection test completed!")
    print("=" * 70)
    
    return len(working), len(failed)


if __name__ == "__main__":
    try:
        working, failed = test_proxy_pool(max_proxies=30, workers=15)
        
        if working > 0:
            print(f"\n✅ Found {working} working proxies - ready to use!")
            sys.exit(0)
        else:
            print("\n⚠️  No working proxies found - may need to try more or use different sources")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

