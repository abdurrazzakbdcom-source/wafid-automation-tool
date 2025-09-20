from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from fake_useragent import UserAgent
from .logger import logger
from .network_monitor import NetworkMonitor


class BrowserAutomation:
    """Manages browser sessions with fresh startup and DOM detection"""
    
    def __init__(self, headless: bool = False):
        self.driver = None
        self.headless = headless
        self.network_monitor = None
        self.detected_fields = {}
        self.user_agent = UserAgent()
        
    def create_fresh_session(self, proxy: Optional[str] = None) -> bool:
        """Create a completely fresh browser session"""
        try:
            # Close existing session if any
            self.close_session()
            
            # Chrome options for fresh session
            chrome_options = Options()
            
            # Headless mode
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # Fresh session arguments
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--no-default-browser-check')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-translate')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            
            # Codespace/Container environment fixes
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-gpu-sandbox')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--remote-debugging-port=9222')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-css3d')
            chrome_options.add_argument('--disable-webgl')
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=4096')
            
            # Privacy and security
            chrome_options.add_argument('--incognito')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Proxy configuration
            if proxy:
                chrome_options.add_argument(f'--proxy-server=http://{proxy}')
                logger.info(f"Browser configured with proxy: {proxy}")
            
            # Random user agent
            user_agent = self.user_agent.random
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            # Window size
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Data directory (fresh temp directory with timestamp)
            import tempfile
            import time
            temp_dir = tempfile.mkdtemp(prefix=f'chrome_session_{int(time.time())}_')
            chrome_options.add_argument(f'--user-data-dir={temp_dir}')
            
            # Additional prefs for fresh session
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,
                    "media_stream": 2,
                },
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2,
                "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Performance optimization
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Create driver
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Additional session cleanup
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            self.driver.delete_all_cookies()
            
            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            
            # Initialize network monitor
            self.network_monitor = NetworkMonitor(self.driver)
            
            logger.browser_fresh_session()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create fresh browser session: {e}")
            return False
    
    def close_session(self):
        """Close current browser session and cleanup"""
        try:
            if self.driver:
                # Clear all data before closing
                self.driver.execute_script("window.localStorage.clear();")
                self.driver.execute_script("window.sessionStorage.clear();")
                self.driver.delete_all_cookies()
                
                # Close browser
                self.driver.quit()
                self.driver = None
                
                logger.debug("Browser session closed and cleaned up")
        except Exception as e:
            logger.warning(f"Error closing browser session: {e}")
    
    def navigate_to_page(self, url: str) -> bool:
        """Navigate to the booking page"""
        try:
            if not self.driver:
                logger.error("Browser session not initialized")
                return False
            
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Page loaded successfully")
            return True
            
        except TimeoutException:
            logger.error("Page load timeout")
            return False
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    def detect_form_fields(self) -> Dict[str, Dict]:
        """Detect all form fields on the page"""
        if not self.driver:
            logger.error("Browser session not initialized")
            return {}
        
        detected_fields = {}
        
        try:
            # Wait for form elements to load
            time.sleep(2)
            
            # Find all form elements
            form_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "input, select, textarea, button[type='submit']")
            
            for element in form_elements:
                try:
                    # Get element attributes
                    tag_name = element.tag_name
                    element_id = element.get_attribute('id') or ''
                    name = element.get_attribute('name') or ''
                    element_type = element.get_attribute('type') or ''
                    placeholder = element.get_attribute('placeholder') or ''
                    label_text = ''
                    
                    # Try to find associated label
                    try:
                        if element_id:
                            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{element_id}']")
                            label_text = label.text.strip()
                    except NoSuchElementException:
                        pass
                    
                    # Create selector
                    if element_id:
                        selector = f"#{element_id}"
                    elif name:
                        selector = f"[name='{name}']"
                    else:
                        selector = f"{tag_name}[type='{element_type}']" if element_type else tag_name
                    
                    # Determine field purpose based on attributes
                    field_purpose = self._determine_field_purpose(
                        element_id, name, placeholder, label_text, element_type
                    )
                    
                    if field_purpose:
                        field_info = {
                            'selector': selector,
                            'tag': tag_name,
                            'type': element_type,
                            'id': element_id,
                            'name': name,
                            'placeholder': placeholder,
                            'label': label_text,
                            'visible': element.is_displayed(),
                            'enabled': element.is_enabled()
                        }
                        
                        detected_fields[field_purpose] = field_info
                        logger.dom_field_detected(field_purpose, selector)
                
                except Exception as e:
                    logger.debug(f"Error processing form element: {e}")
                    continue
            
            # Detect hidden inputs (tokens, CSRF values)
            hidden_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='hidden']")
            for hidden in hidden_inputs:
                try:
                    name = hidden.get_attribute('name') or ''
                    value = hidden.get_attribute('value') or ''
                    
                    if name and ('token' in name.lower() or 'csrf' in name.lower() or '_token' in name.lower()):
                        field_info = {
                            'selector': f"input[name='{name}']",
                            'tag': 'input',
                            'type': 'hidden',
                            'name': name,
                            'value': value,
                            'visible': False,
                            'enabled': True
                        }
                        
                        detected_fields[f'hidden_{name}'] = field_info
                        logger.dom_field_detected(f'hidden_{name}', f"input[name='{name}']")
                        
                except Exception as e:
                    logger.debug(f"Error processing hidden input: {e}")
            
            self.detected_fields = detected_fields
            logger.info(f"Detected {len(detected_fields)} form fields")
            
            return detected_fields
            
        except Exception as e:
            logger.error(f"Form field detection failed: {e}")
            return {}
    
    def _determine_field_purpose(self, element_id: str, name: str, placeholder: str, 
                                label: str, input_type: str) -> str:
        """Determine the purpose of a form field based on its attributes"""
        
        # Combine all text for analysis
        all_text = f"{element_id} {name} {placeholder} {label}".lower()
        
        # Field mapping based on common patterns
        field_mappings = {
            'country': ['country', 'nation', 'citizenship'],
            'city': ['city', 'town', 'location'],
            'country_traveling_to': ['traveling', 'destination', 'travel_to'],
            'first_name': ['firstname', 'first_name', 'fname', 'given_name'],
            'last_name': ['lastname', 'last_name', 'lname', 'surname', 'family_name'],
            'date_of_birth': ['birth', 'dob', 'born', 'birthday'],
            'nationality': ['nationality', 'citizen'],
            'gender': ['gender', 'sex'],
            'marital_status': ['marital', 'marriage', 'married'],
            'passport_number': ['passport', 'passport_num', 'passport_no'],
            'passport_issue_date': ['passport.*issue', 'issue.*date'],
            'passport_issue_place': ['passport.*place', 'issue.*place'],
            'passport_expiry': ['passport.*expir', 'expir.*date'],
            'visa_type': ['visa', 'visa_type'],
            'email': ['email', 'mail'],
            'phone': ['phone', 'mobile', 'tel'],
            'national_id': ['national.*id', 'id.*number', 'civil.*id'],
            'position': ['position', 'job', 'occupation', 'profession']
        }
        
        # Check for matches
        for field_purpose, patterns in field_mappings.items():
            for pattern in patterns:
                if pattern in all_text:
                    return field_purpose
        
        # Special cases for input types
        if input_type == 'email':
            return 'email'
        elif input_type == 'tel':
            return 'phone'
        elif input_type == 'date':
            if 'birth' in all_text:
                return 'date_of_birth'
            elif 'expir' in all_text:
                return 'passport_expiry'
            elif 'issue' in all_text:
                return 'passport_issue_date'
        
        return ''  # Unknown field purpose
    
    def fill_field(self, field_purpose: str, value: str) -> bool:
        """Fill a form field by its purpose"""
        if not self.driver or field_purpose not in self.detected_fields:
            logger.warning(f"Field '{field_purpose}' not found")
            return False
        
        try:
            field_info = self.detected_fields[field_purpose]
            selector = field_info['selector']
            tag = field_info['tag']
            
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView();", element)
            time.sleep(0.5)
            
            # Fill based on element type
            if tag == 'select':
                select = Select(element)
                # Try to select by visible text first, then by value
                try:
                    select.select_by_visible_text(value)
                except:
                    select.select_by_value(value)
            
            elif tag == 'input' and field_info['type'] == 'checkbox':
                if value.lower() in ['true', '1', 'yes', 'checked']:
                    if not element.is_selected():
                        element.click()
            
            else:
                # Clear and type value
                element.clear()
                element.send_keys(value)
            
            logger.form_field_filled(field_purpose, value)
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill field '{field_purpose}': {e}")
            return False
    
    def click_element(self, selector: str) -> bool:
        """Click an element by CSS selector"""
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView();", element)
            time.sleep(0.5)
            
            element.click()
            logger.debug(f"Clicked element: {selector}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click element '{selector}': {e}")
            return False
    
    def wait_for_response(self, timeout: int = 30) -> Optional[Dict]:
        """Wait for and capture network response"""
        if not self.network_monitor:
            logger.error("Network monitor not initialized")
            return None
        
        return self.network_monitor.wait_for_response(timeout)
    
    def get_page_source(self) -> str:
        """Get current page source"""
        if not self.driver:
            return ""
        return self.driver.page_source
    
    def get_current_url(self) -> str:
        """Get current page URL"""
        if not self.driver:
            return ""
        return self.driver.current_url
    
    def take_screenshot(self, filename: str) -> bool:
        """Take a screenshot of current page"""
        try:
            if not self.driver:
                return False
            
            self.driver.save_screenshot(filename)
            logger.debug(f"Screenshot saved: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return False