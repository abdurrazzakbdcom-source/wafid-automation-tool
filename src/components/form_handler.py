import pandas as pd
import time
from typing import Dict, List, Optional, Any
from .logger import logger
from .browser_automation import BrowserAutomation
from .network_monitor import NetworkMonitor


class FormHandler:
    """Handles form filling and submission for wafid.com booking"""
    
    def __init__(self, browser: BrowserAutomation):
        self.browser = browser
        self.candidate_data = {}
        self.appointment_data = {}
        
    def load_candidate_data(self, csv_file: str) -> bool:
        """Load candidate data from CSV file"""
        try:
            df = pd.read_csv(csv_file)
            
            if len(df) == 0:
                logger.error("CSV file is empty")
                return False
            
            # Use first row as candidate data
            row = df.iloc[0]
            
            self.candidate_data = {
                'appointment_location': row.get('Appointment_Location', ''),
                'country': row.get('Country', ''),
                'city': row.get('City', ''),
                'country_traveling_to': row.get('Country_Traveling_To', ''),
                'first_name': row.get('First_Name', ''),
                'last_name': row.get('Last_Name', ''),
                'date_of_birth': row.get('Date_Of_Birth', ''),
                'nationality': row.get('Nationality', ''),
                'gender': row.get('Gender', ''),
                'marital_status': row.get('Marital_Status', ''),
                'passport_number': row.get('Passport_Number', ''),
                'confirm_passport_number': row.get('Confirm_Passport_Number', ''),
                'passport_issue_date': row.get('Passport_Issue_Date', ''),
                'passport_issue_place': row.get('Passport_Issue_Place', ''),
                'passport_expiry_date': row.get('Passport_Expiry_Date', ''),
                'visa_type': row.get('Visa_Type', ''),
                'email_address': row.get('Email_Address', ''),
                'phone': row.get('Phone', ''),
                'national_id': row.get('National_ID', ''),
                'position_applied_for': row.get('Position_Applied_For', '')
            }
            
            # Split into appointment and candidate info
            self.appointment_data = {
                'country': self.candidate_data['country'],
                'city': self.candidate_data['city'],
                'country_traveling_to': self.candidate_data['country_traveling_to']
            }
            
            logger.info(f"Loaded candidate data: {self.candidate_data['first_name']} {self.candidate_data['last_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load candidate data: {e}")
            return False
    
    def fill_appointment_info(self) -> bool:
        """Fill only appointment information (Country, City, Country Traveling To)"""
        try:
            logger.info("Filling appointment information...")
            
            # Fill country
            if self.appointment_data.get('country'):
                success = self.browser.fill_field('country', self.appointment_data['country'])
                if not success:
                    logger.warning("Failed to fill country field")
                time.sleep(1)
            
            # Fill city  
            if self.appointment_data.get('city'):
                success = self.browser.fill_field('city', self.appointment_data['city'])
                if not success:
                    logger.warning("Failed to fill city field")
                time.sleep(1)
            
            # Fill country traveling to
            if self.appointment_data.get('country_traveling_to'):
                success = self.browser.fill_field('country_traveling_to', self.appointment_data['country_traveling_to'])
                if not success:
                    logger.warning("Failed to fill country traveling to field")
                time.sleep(1)
            
            # Select Standard Appointment if option exists
            standard_appointment_selectors = [
                "input[value*='standard']",
                "input[type='radio'][value*='Standard']",
                "select option[value*='standard']",
                "[data-value*='standard']"
            ]
            
            for selector in standard_appointment_selectors:
                try:
                    if self.browser.click_element(selector):
                        logger.info("Selected Standard Appointment")
                        break
                except:
                    continue
            
            logger.info("Appointment information filled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill appointment information: {e}")
            return False
    
    def submit_appointment_form(self) -> Optional[Dict]:
        """Submit appointment form and wait for response"""
        try:
            logger.info("Submitting appointment form...")
            
            # Find and click submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Submit')",
                "button:contains('Continue')",
                "button:contains('Next')",
                ".submit-btn",
                "#submit",
                "#continue"
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    if self.browser.click_element(selector):
                        logger.info(f"Clicked submit button: {selector}")
                        submitted = True
                        break
                except:
                    continue
            
            if not submitted:
                logger.error("Could not find submit button")
                return None
            
            # Wait for response
            logger.info("Waiting for server response...")
            response = self.browser.wait_for_response(timeout=30)
            
            if response:
                logger.info("Received server response")
                return response
            else:
                logger.warning("No response received from server")
                return None
                
        except Exception as e:
            logger.error(f"Failed to submit appointment form: {e}")
            return None
    
    def extract_medical_center(self, response: Dict) -> Optional[str]:
        """Extract assigned medical center from server response"""
        try:
            if not response:
                return None
            
            # Use network monitor to extract medical center
            if self.browser.network_monitor:
                center_name = self.browser.network_monitor.extract_medical_center(response)
                if center_name:
                    return center_name
            
            # Manual extraction as fallback
            possible_fields = [
                'assignedMedicalCenter',
                'medical_center',
                'medicalCenter',
                'clinic_name',
                'center_name',
                'hospital_name',
                'assigned_center',
                'appointment_center',
                'clinic',
                'center',
                'hospital'
            ]
            
            def search_recursive(data, fields):
                if isinstance(data, dict):
                    for field in fields:
                        if field in data:
                            return str(data[field])
                    
                    for value in data.values():
                        result = search_recursive(value, fields)
                        if result:
                            return result
                
                elif isinstance(data, list):
                    for item in data:
                        result = search_recursive(item, fields)
                        if result:
                            return result
                
                return None
            
            center_name = search_recursive(response, possible_fields)
            
            if center_name:
                logger.medical_center_assigned(center_name)
                return center_name
            
            logger.warning("Could not extract medical center from response")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract medical center: {e}")
            return None
    
    def fill_candidate_info(self) -> bool:
        """Fill all candidate information"""
        try:
            logger.info("Filling candidate information...")
            
            # Map candidate data to form fields
            field_mappings = {
                'first_name': self.candidate_data.get('first_name', ''),
                'last_name': self.candidate_data.get('last_name', ''),
                'date_of_birth': self.candidate_data.get('date_of_birth', ''),
                'nationality': self.candidate_data.get('nationality', ''),
                'gender': self.candidate_data.get('gender', ''),
                'marital_status': self.candidate_data.get('marital_status', ''),
                'passport_number': self.candidate_data.get('passport_number', ''),
                'passport_issue_date': self.candidate_data.get('passport_issue_date', ''),
                'passport_issue_place': self.candidate_data.get('passport_issue_place', ''),
                'passport_expiry': self.candidate_data.get('passport_expiry_date', ''),
                'visa_type': self.candidate_data.get('visa_type', ''),
                'email': self.candidate_data.get('email_address', ''),
                'phone': self.candidate_data.get('phone', ''),
                'national_id': self.candidate_data.get('national_id', ''),
                'position': self.candidate_data.get('position_applied_for', '')
            }
            
            # Fill each field
            filled_count = 0
            for field_purpose, value in field_mappings.items():
                if value:
                    success = self.browser.fill_field(field_purpose, str(value))
                    if success:
                        filled_count += 1
                    time.sleep(0.5)  # Small delay between fields
            
            # Fill confirm passport number (same as passport number)
            if self.candidate_data.get('passport_number'):
                self.browser.fill_field('passport_number', self.candidate_data['passport_number'])
            
            logger.info(f"Filled {filled_count} candidate information fields")
            
            # Tick required checkboxes
            self._tick_required_checkboxes()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill candidate information: {e}")
            return False
    
    def _tick_required_checkboxes(self):
        """Tick commonly required checkboxes"""
        try:
            # Common checkbox patterns for terms and conditions
            checkbox_selectors = [
                "input[type='checkbox'][name*='terms']",
                "input[type='checkbox'][name*='agree']",
                "input[type='checkbox'][name*='accept']",
                "input[type='checkbox'][name*='condition']",
                "input[type='checkbox'][name*='privacy']",
                "input[type='checkbox'][id*='terms']",
                "input[type='checkbox'][id*='agree']",
                "input[type='checkbox'][id*='accept']"
            ]
            
            for selector in checkbox_selectors:
                try:
                    if self.browser.click_element(selector):
                        logger.debug(f"Ticked checkbox: {selector}")
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error ticking checkboxes: {e}")
    
    def submit_final_form(self) -> Optional[str]:
        """Submit final form and capture payment page URL"""
        try:
            logger.info("Submitting final form...")
            
            # Find and click final submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Submit')",
                "button:contains('Book')",
                "button:contains('Confirm')",
                "button:contains('Pay')",
                ".submit-btn",
                ".book-btn",
                "#submit",
                "#book",
                "#confirm"
            ]
            
            for selector in submit_selectors:
                try:
                    if self.browser.click_element(selector):
                        logger.info(f"Clicked final submit button: {selector}")
                        break
                except:
                    continue
            
            # Wait for page navigation
            time.sleep(5)
            
            # Get current URL (should be payment page)
            current_url = self.browser.get_current_url()
            
            # Check if this looks like a payment URL
            payment_indicators = ['payment', 'pay', 'checkout', 'billing', 'invoice']
            
            if any(indicator in current_url.lower() for indicator in payment_indicators):
                logger.payment_url_captured(current_url)
                return current_url
            else:
                logger.warning(f"Current URL doesn't look like payment page: {current_url}")
                return current_url  # Return anyway, might still be useful
                
        except Exception as e:
            logger.error(f"Failed to submit final form: {e}")
            return None
    
    def save_payment_url(self, url: str, csv_file: str = "data/payment_urls.csv"):
        """Save payment URL to CSV file"""
        try:
            import os
            from datetime import datetime
            
            # Create data structure
            payment_data = {
                'timestamp': datetime.now().isoformat(),
                'candidate_name': f"{self.candidate_data.get('first_name', '')} {self.candidate_data.get('last_name', '')}",
                'email': self.candidate_data.get('email_address', ''),
                'passport_number': self.candidate_data.get('passport_number', ''),
                'payment_url': url,
                'country': self.appointment_data.get('country', ''),
                'city': self.appointment_data.get('city', ''),
                'country_traveling_to': self.appointment_data.get('country_traveling_to', '')
            }
            
            # Check if file exists
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                df = pd.concat([df, pd.DataFrame([payment_data])], ignore_index=True)
            else:
                df = pd.DataFrame([payment_data])
            
            # Save to CSV
            df.to_csv(csv_file, index=False)
            logger.info(f"Payment URL saved to {csv_file}")
            
        except Exception as e:
            logger.error(f"Failed to save payment URL: {e}")
    
    def get_candidate_summary(self) -> str:
        """Get summary of current candidate data"""
        if not self.candidate_data:
            return "No candidate data loaded"
        
        return f"{self.candidate_data.get('first_name', '')} {self.candidate_data.get('last_name', '')} - {self.candidate_data.get('email_address', '')}"