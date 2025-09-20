import requests
import json
import time
import random
import threading
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from .logger import logger


class ProxyManager:
    """Manages proxy IPs with fetching, testing, and validation"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.proxy_file = os.path.join(data_dir, "working_proxies.json")
        self.working_proxies = []
        self.used_proxies = set()
        self.current_proxy = None
        self.lock = threading.Lock()
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing working proxies
        self.load_working_proxies()
        
        # If no working proxies, add some known fast ones to start
        if not self.working_proxies:
            self._add_starter_proxies()
    
    def load_working_proxies(self):
        """Load working proxies from file"""
        try:
            if os.path.exists(self.proxy_file):
                with open(self.proxy_file, 'r') as f:
                    data = json.load(f)
                    self.working_proxies = data.get('proxies', [])
                    logger.info(f"Loaded {len(self.working_proxies)} working proxies from file")
            else:
                logger.info("No existing proxy file found")
        except Exception as e:
            logger.error(f"Failed to load working proxies: {e}")
            self.working_proxies = []
    
    def _add_starter_proxies(self):
        """Add some starter proxies that are commonly working"""
        starter_proxies = [
            "185.221.160.0:80",
            "104.17.22.98:80",
            "104.21.38.99:80",
            "45.131.6.215:80",
            "104.17.79.219:80"
        ]
        
        logger.info("Adding starter proxies for immediate use...")
        for proxy in starter_proxies:
            proxy_info = {
                'proxy': proxy,
                'response_time': 0.1,  # Default response time
                'tested_at': time.time(),
                'success_count': 1,
                'failure_count': 0
            }
            self.working_proxies.append(proxy_info)
        
        logger.info(f"Added {len(starter_proxies)} starter proxies")
    
    def save_working_proxies(self):
        """Save working proxies to file"""
        try:
            data = {
                'proxies': self.working_proxies,
                'last_updated': time.time(),
                'total_count': len(self.working_proxies)
            }
            with open(self.proxy_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.working_proxies)} working proxies to file")
        except Exception as e:
            logger.error(f"Failed to save working proxies: {e}")
    
    def fetch_proxies_from_sources(self) -> List[str]:
        """Fetch proxy lists from fast, reliable sources - optimized for quick automation"""
        proxy_sources = [
            # Only use the fastest, most reliable sources
            "https://api.proxyscrape.com/v2/?request=get&format=textplain&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
        ]
        
        all_proxies = []
        
        logger.info("Fetching proxies from open-source lists...")
        
        for source in proxy_sources:
            try:
                logger.debug(f"Fetching from: {source}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(source, timeout=15, headers=headers)
                
                if response.status_code == 200:
                    # Handle different response formats
                    proxies = self._parse_proxy_response(response, source)
                    valid_proxies = [p.strip() for p in proxies if self._is_valid_proxy_format(p.strip())]
                    all_proxies.extend(valid_proxies)
                    logger.info(f"Fetched {len(valid_proxies)} proxies from {source}")
                else:
                    logger.warning(f"Failed to fetch from {source}: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Error fetching from {source}: {e}")
        
        # Remove duplicates
        unique_proxies = list(set(all_proxies))
        logger.info(f"Total unique proxies fetched: {len(unique_proxies)}")
        
        return unique_proxies
    
    def _parse_proxy_response(self, response, source_url: str) -> List[str]:
        """Parse proxy response based on content type and source"""
        try:
            content_type = response.headers.get('content-type', '').lower()
            
            # Handle JSON responses (like geonode API)
            if 'json' in content_type or 'geonode.com' in source_url:
                try:
                    json_data = response.json()
                    proxies = []
                    
                    # Handle geonode format
                    if isinstance(json_data, dict) and 'data' in json_data:
                        for proxy_data in json_data['data']:
                            if isinstance(proxy_data, dict):
                                ip = proxy_data.get('ip', '')
                                port = proxy_data.get('port', '')
                                if ip and port:
                                    proxies.append(f"{ip}:{port}")
                    
                    # Handle other JSON formats
                    elif isinstance(json_data, list):
                        for item in json_data:
                            if isinstance(item, dict):
                                ip = item.get('ip', item.get('host', ''))
                                port = item.get('port', '')
                                if ip and port:
                                    proxies.append(f"{ip}:{port}")
                    
                    return proxies
                except json.JSONDecodeError:
                    pass
            
            # Handle plain text responses
            return response.text.strip().split('\n')
            
        except Exception as e:
            logger.debug(f"Error parsing response from {source_url}: {e}")
            return response.text.strip().split('\n')
    
    def _is_valid_proxy_format(self, proxy: str) -> bool:
        """Check if proxy string has valid format (IP:PORT)"""
        try:
            if ':' not in proxy:
                return False
            
            ip, port = proxy.split(':', 1)
            
            # Basic IP validation
            ip_parts = ip.split('.')
            if len(ip_parts) != 4:
                return False
            
            for part in ip_parts:
                if not part.isdigit() or not 0 <= int(part) <= 255:
                    return False
            
            # Port validation
            if not port.isdigit() or not 1 <= int(port) <= 65535:
                return False
            
            return True
        except:
            return False
    
    def test_proxy(self, proxy: str, timeout: int = 8) -> Tuple[bool, float, str]:
        """Test a single proxy and return (success, response_time, error_message)"""
        start_time = time.time()
        
        try:
            # Test URLs to verify proxy functionality - using more reliable endpoints
            test_urls = [
                "http://httpbin.org/ip",
                "http://icanhazip.com",
                "http://ident.me",
                "https://api.ipify.org?format=json",
                "http://checkip.amazonaws.com"
            ]
            
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            for test_url in test_urls:
                try:
                    response = requests.get(
                        test_url,
                        proxies=proxy_dict,
                        timeout=timeout,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )
                    
                    if response.status_code == 200:
                        response_time = time.time() - start_time
                        return True, response_time, ""
                        
                except requests.RequestException:
                    continue
            
            response_time = time.time() - start_time
            return False, response_time, "All test URLs failed"
            
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, str(e)
    
    def test_proxies_batch(self, proxies: List[str], max_workers: int = 50) -> List[Dict]:
        """Test multiple proxies concurrently"""
        working_proxies = []
        
        logger.info(f"Testing {len(proxies)} proxies with {max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all proxy tests
            future_to_proxy = {
                executor.submit(self.test_proxy, proxy): proxy 
                for proxy in proxies
            }
            
            completed = 0
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                completed += 1
                
                try:
                    success, response_time, error = future.result()
                    
                    if success:
                        proxy_info = {
                            'proxy': proxy,
                            'response_time': response_time,
                            'tested_at': time.time(),
                            'success_count': 1,
                            'failure_count': 0
                        }
                        working_proxies.append(proxy_info)
                        logger.proxy_success(proxy, response_time)
                    else:
                        logger.proxy_failure(proxy, error)
                        
                except Exception as e:
                    logger.proxy_failure(proxy, f"Test error: {e}")
                
                # Progress update every 50 tests
                if completed % 50 == 0:
                    logger.info(f"Tested {completed}/{len(proxies)} proxies...")
        
        logger.info(f"Testing completed. {len(working_proxies)} working proxies found.")
        return working_proxies
    
    def refresh_proxy_list(self, min_working_proxies: int = 5):
        """Fetch and test new proxies to maintain minimum working proxy count - optimized for speed"""
        with self.lock:
            current_count = len(self.working_proxies)
            
            if current_count >= min_working_proxies:
                logger.info(f"Sufficient working proxies available: {current_count}")
                return
            
            logger.info(f"Need more proxies. Current: {current_count}, Required: {min_working_proxies}")
            
            # Fetch new proxies
            new_proxies = self.fetch_proxies_from_sources()
            
            if not new_proxies:
                logger.warning("No new proxies fetched from sources")
                return
            
            # Filter out already known working proxies
            existing_proxy_ips = {p['proxy'] for p in self.working_proxies}
            new_proxies = [p for p in new_proxies if p not in existing_proxy_ips]
            
            if not new_proxies:
                logger.info("All fetched proxies are already in working list")
                return
            
            # LIMIT TO FIRST 50 PROXIES FOR FAST TESTING
            new_proxies = new_proxies[:50]
            logger.info(f"Testing first {len(new_proxies)} proxies for quick automation start...")
            
            # Test new proxies
            tested_proxies = self.test_proxies_batch(new_proxies, max_workers=20)
            
            # Add working proxies to list
            self.working_proxies.extend(tested_proxies)
            
            # Sort by response time (fastest first)
            self.working_proxies.sort(key=lambda x: x['response_time'])
            
            # Save to file
            self.save_working_proxies()
            
            logger.info(f"Updated proxy list. Total working proxies: {len(self.working_proxies)}")
            
            # If we still don't have enough, we'll use what we have
            if len(self.working_proxies) < min_working_proxies:
                logger.warning(f"Only found {len(self.working_proxies)} working proxies, but continuing with automation")
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next available proxy that hasn't been used"""
        with self.lock:
            # If no working proxies, try to refresh
            if not self.working_proxies:
                logger.warning("No working proxies available. Attempting to refresh...")
                self.refresh_proxy_list()
            
            # Find unused proxy
            for proxy_info in self.working_proxies:
                proxy = proxy_info['proxy']
                if proxy not in self.used_proxies:
                    self.used_proxies.add(proxy)
                    self.current_proxy = proxy
                    logger.info(f"Selected proxy: {proxy}")
                    return proxy
            
            # If all proxies used, reset used list and get first one
            if self.working_proxies:
                logger.info("All proxies used. Resetting used list...")
                self.used_proxies.clear()
                proxy = self.working_proxies[0]['proxy']
                self.used_proxies.add(proxy)
                self.current_proxy = proxy
                logger.info(f"Selected proxy (reset): {proxy}")
                return proxy
            
            logger.error("No working proxies available")
            return None
    
    def get_current_proxy(self) -> Optional[str]:
        """Get currently selected proxy"""
        return self.current_proxy
    
    def mark_proxy_failed(self, proxy: str):
        """Mark a proxy as failed and remove from working list"""
        with self.lock:
            # Remove from working proxies
            self.working_proxies = [p for p in self.working_proxies if p['proxy'] != proxy]
            
            # Remove from used proxies
            self.used_proxies.discard(proxy)
            
            # Clear current proxy if it was the failed one
            if self.current_proxy == proxy:
                self.current_proxy = None
            
            logger.warning(f"Removed failed proxy: {proxy}")
            self.save_working_proxies()
    
    def get_proxy_stats(self) -> Dict:
        """Get proxy statistics"""
        with self.lock:
            return {
                'total_working': len(self.working_proxies),
                'used_count': len(self.used_proxies),
                'current_proxy': self.current_proxy,
                'available_count': len(self.working_proxies) - len(self.used_proxies)
            }
    
    def get_proxy_dict(self, proxy: str) -> Dict[str, str]:
        """Convert proxy string to requests proxy dictionary"""
        if not proxy:
            return {}
        
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }