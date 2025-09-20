import time
import random
from typing import Dict, List, Optional, Any, Callable
from .logger import logger
from .proxy_manager import ProxyManager
from .browser_automation import BrowserAutomation
from .form_handler import FormHandler


class AutomationEngine:
    """Main automation engine with matching logic and retry mechanism"""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.browser = BrowserAutomation()
        self.form_handler = FormHandler(self.browser)
        
        # Configuration
        self.target_medical_center = ""
        self.booking_url = "https://wafid.com/book-appointment"
        self.max_retries = 100  # Maximum retry attempts
        self.retry_count = 0
        
        # State
        self.is_running = False
        self.success_callback = None
        self.status_callback = None
        
        # Statistics
        self.stats = {
            'attempts': 0,
            'matches_found': 0,
            'proxies_used': 0,
            'total_time': 0
        }
    
    def set_target_medical_center(self, center_name: str):
        """Set the target medical center to match"""
        self.target_medical_center = center_name.strip()
        logger.info(f"Target medical center set: {self.target_medical_center}")
    
    def set_callbacks(self, success_callback: Callable = None, status_callback: Callable = None):
        """Set callback functions for success and status updates"""
        self.success_callback = success_callback
        self.status_callback = status_callback
    
    def load_candidate_data(self, csv_file: str) -> bool:
        """Load candidate data from CSV"""
        return self.form_handler.load_candidate_data(csv_file)
    
    def start_automation(self) -> bool:
        """Start the automation process"""
        if not self.target_medical_center:
            logger.error("Target medical center not set")
            return False
        
        if not self.form_handler.candidate_data:
            logger.error("Candidate data not loaded")
            return False
        
        self.is_running = True
        self.retry_count = 0
        self.stats['attempts'] = 0
        self.stats['total_time'] = time.time()
        
        logger.automation_started(self.target_medical_center)
        
        try:
            # Ensure we have working proxies
            self.proxy_manager.refresh_proxy_list(min_working_proxies=5)
            
            # Start automation loop
            success = self._automation_loop()
            
            if success:
                logger.info("Automation completed successfully!")
                if self.success_callback:
                    self.success_callback()
            else:
                logger.warning("Automation stopped without success")
            
            return success
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            return False
        finally:
            self.is_running = False
            self.stats['total_time'] = time.time() - self.stats['total_time']
    
    def stop_automation(self):
        """Stop the automation process"""
        self.is_running = False
        logger.automation_stopped()
    
    def _automation_loop(self) -> bool:
        """Main automation loop with retry mechanism"""
        
        while self.is_running and self.retry_count < self.max_retries:
            self.retry_count += 1
            self.stats['attempts'] = self.retry_count
            
            logger.info(f"Starting attempt #{self.retry_count}")
            
            if self.status_callback:
                self.status_callback(f"Attempt {self.retry_count}/{self.max_retries}")
            
            try:
                # Step 1: Get fresh proxy
                proxy = self.proxy_manager.get_next_proxy()
                if not proxy:
                    logger.error("No working proxies available")
                    time.sleep(5)
                    continue
                
                self.stats['proxies_used'] += 1
                
                # Step 2: Create fresh browser session
                if not self.browser.create_fresh_session(proxy):
                    logger.warning("Failed to create browser session, trying next proxy")
                    self.proxy_manager.mark_proxy_failed(proxy)
                    continue
                
                # Step 3: Navigate to booking page
                if not self.browser.navigate_to_page(self.booking_url):
                    logger.warning("Failed to navigate to booking page")
                    self.browser.close_session()
                    continue
                
                # Step 4: Research phase - detect form fields
                if not self._research_phase():
                    logger.warning("Research phase failed")
                    self.browser.close_session()
                    continue
                
                # Step 5: Fill appointment information only
                if not self.form_handler.fill_appointment_info():
                    logger.warning("Failed to fill appointment information")
                    self.browser.close_session()
                    continue
                
                # Step 6: Submit appointment form and get response
                response = self.form_handler.submit_appointment_form()
                if not response:
                    logger.warning("No response received from appointment submission")
                    self.browser.close_session()
                    continue
                
                # Step 7: Extract assigned medical center from LIVE response
                assigned_center = self.form_handler.extract_medical_center(response)
                if not assigned_center:
                    logger.warning("Could not extract medical center from response")
                    self.browser.close_session()
                    continue
                
                # Step 8: Compare with target medical center
                if self._check_medical_center_match(assigned_center):
                    # MATCH FOUND!
                    logger.medical_center_match(assigned_center, self.target_medical_center)
                    self.stats['matches_found'] += 1
                    
                    # Fill candidate information and submit
                    if self._complete_booking():
                        return True  # Success!
                    else:
                        logger.error("Failed to complete booking despite match")
                        self.browser.close_session()
                        continue
                else:
                    # No match - retry with new proxy
                    logger.medical_center_mismatch(assigned_center, self.target_medical_center)
                    self.browser.close_session()
                    
                    # Small delay before retry
                    time.sleep(random.uniform(1, 3))
                    continue
                    
            except Exception as e:
                logger.error(f"Error in automation loop attempt #{self.retry_count}: {e}")
                self.browser.close_session()
                time.sleep(2)
                continue
        
        # If we get here, we've exceeded max retries
        logger.warning(f"Maximum retries ({self.max_retries}) reached without finding match")
        return False
    
    def _research_phase(self) -> bool:
        """Research phase - detect form fields and monitor network"""
        try:
            logger.info("Starting research phase...")
            
            # Detect form fields
            detected_fields = self.browser.detect_form_fields()
            
            if not detected_fields:
                logger.warning("No form fields detected")
                return False
            
            logger.info(f"Research phase completed - {len(detected_fields)} fields detected")
            return True
            
        except Exception as e:
            logger.error(f"Research phase failed: {e}")
            return False
    
    def _check_medical_center_match(self, assigned_center: str) -> bool:
        """Check if assigned medical center matches target"""
        try:
            # Clean and normalize strings for comparison
            assigned_clean = assigned_center.strip().lower()
            target_clean = self.target_medical_center.strip().lower()
            
            # Exact match
            if assigned_clean == target_clean:
                return True
            
            # Contains match (assigned center contains target)
            if target_clean in assigned_clean:
                return True
            
            # Contains match (target contains assigned center)
            if assigned_clean in target_clean:
                return True
            
            # Fuzzy matching for similar names
            if self._fuzzy_match(assigned_clean, target_clean):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking medical center match: {e}")
            return False
    
    def _fuzzy_match(self, assigned: str, target: str, threshold: float = 0.8) -> bool:
        """Fuzzy string matching for medical center names"""
        try:
            # Simple fuzzy matching based on common words
            assigned_words = set(assigned.split())
            target_words = set(target.split())
            
            if not assigned_words or not target_words:
                return False
            
            # Calculate similarity
            intersection = len(assigned_words.intersection(target_words))
            union = len(assigned_words.union(target_words))
            
            if union == 0:
                return False
            
            similarity = intersection / union
            
            return similarity >= threshold
            
        except Exception:
            return False
    
    def _complete_booking(self) -> bool:
        """Complete the booking process after finding a match"""
        try:
            logger.info("Completing booking process...")
            
            # Fill all candidate information
            if not self.form_handler.fill_candidate_info():
                logger.error("Failed to fill candidate information")
                return False
            
            # Submit final form and capture payment URL
            payment_url = self.form_handler.submit_final_form()
            
            if payment_url:
                # Save payment URL
                self.form_handler.save_payment_url(payment_url)
                logger.info("Booking completed successfully!")
                return True
            else:
                logger.error("Failed to capture payment URL")
                return False
                
        except Exception as e:
            logger.error(f"Error completing booking: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get automation statistics"""
        stats = self.stats.copy()
        stats['is_running'] = self.is_running
        stats['current_attempt'] = self.retry_count
        stats['max_retries'] = self.max_retries
        stats['target_center'] = self.target_medical_center
        stats['candidate_summary'] = self.form_handler.get_candidate_summary()
        
        # Proxy statistics
        proxy_stats = self.proxy_manager.get_proxy_stats()
        stats.update(proxy_stats)
        
        return stats
    
    def reset_statistics(self):
        """Reset automation statistics"""
        self.stats = {
            'attempts': 0,
            'matches_found': 0,
            'proxies_used': 0,
            'total_time': 0
        }
        self.retry_count = 0