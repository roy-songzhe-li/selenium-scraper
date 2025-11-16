"""
Proxy validator - tests and caches working proxies
"""
import requests
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


class ProxyValidator:
    
    def __init__(self, cache_file='working_proxies.json', cache_ttl=3600):
        self.cache_file = Path(__file__).parent.parent / cache_file
        self.cache_ttl = cache_ttl  # Cache valid for 1 hour
    
    def test_proxy(self, proxy, timeout=8):
        """Test if a single proxy works"""
        ip = proxy['ip']
        port = proxy['port']
        protocol = proxy['protocol']
        
        if 'socks5' in protocol.lower():
            proxy_url = f"socks5://{ip}:{port}"
        elif 'socks4' in protocol.lower():
            proxy_url = f"socks4://{ip}:{port}"
        elif 'http' in protocol.lower():
            proxy_url = f"http://{ip}:{port}"
        else:
            proxy_url = f"socks5://{ip}:{port}"
        
        try:
            start_time = time.time()
            response = requests.get(
                'http://httpbin.org/ip',
                proxies={'http': proxy_url, 'https': proxy_url},
                timeout=timeout
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                proxy['working'] = True
                proxy['response_time'] = round(elapsed, 2)
                proxy['last_tested'] = time.time()
                return proxy
        except:
            pass
        
        return None
    
    def validate_proxy_list(self, proxy_list, max_workers=20, max_test=100):
        """Validate a list of proxies concurrently"""
        logger.info(f"Validating {min(max_test, len(proxy_list))} proxies...")
        
        working_proxies = []
        test_list = proxy_list[:max_test]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.test_proxy, proxy) for proxy in test_list]
            
            for i, future in enumerate(futures, 1):
                result = future.result()
                if result:
                    working_proxies.append(result)
                    logger.info(f"✅ Found working proxy: {result['ip']}:{result['port']} ({result['response_time']}s)")
                
                if i % 10 == 0:
                    logger.info(f"Tested {i}/{len(test_list)} - Found {len(working_proxies)} working")
        
        logger.info(f"Validation complete: {len(working_proxies)}/{len(test_list)} working ({len(working_proxies)/len(test_list)*100:.1f}%)")
        return working_proxies
    
    def save_cache(self, proxies):
        """Save working proxies to cache"""
        cache_data = {
            'timestamp': time.time(),
            'proxies': proxies
        }
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        logger.info(f"Saved {len(proxies)} working proxies to cache")
    
    def load_cache(self):
        """Load working proxies from cache if valid"""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            timestamp = cache_data.get('timestamp', 0)
            age = time.time() - timestamp
            
            if age < self.cache_ttl:
                proxies = cache_data.get('proxies', [])
                logger.info(f"Loaded {len(proxies)} proxies from cache (age: {age/60:.1f}min)")
                return proxies
            else:
                logger.info(f"Cache expired (age: {age/60:.1f}min > {self.cache_ttl/60:.1f}min)")
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
        
        return None
    
    def get_working_proxies(self, proxy_list, force_refresh=False):
        """Get working proxies (use cache if available)"""
        if not force_refresh:
            cached = self.load_cache()
            if cached:
                return cached
        
        # Validate proxies
        working = self.validate_proxy_list(proxy_list, max_workers=20, max_test=100)
        
        if working:
            self.save_cache(working)
        
        return working

