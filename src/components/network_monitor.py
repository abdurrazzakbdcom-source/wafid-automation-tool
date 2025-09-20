import json
import time
from typing import Dict, List, Optional, Any
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from .logger import logger


class NetworkMonitor:
    """Monitors network requests and responses for the browser"""
    
    def __init__(self, driver):
        self.driver = driver
        self.requests = []
        self.responses = []
        self.last_response = None
        
        # Enable logging for Chrome DevTools
        self._enable_network_logging()
    
    def _enable_network_logging(self):
        """Enable network logging in Chrome DevTools"""
        try:
            # Enable Network domain
            self.driver.execute_cdp_cmd('Network.enable', {})
            
            # Enable Runtime domain for console events
            self.driver.execute_cdp_cmd('Runtime.enable', {})
            
            logger.debug("Network monitoring enabled")
        except Exception as e:
            logger.warning(f"Could not enable network monitoring: {e}")
    
    def get_network_logs(self) -> List[Dict]:
        """Get all network logs from Chrome DevTools"""
        try:
            logs = self.driver.get_log('performance')
            network_logs = []
            
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'].startswith('Network.'):
                    network_logs.append(message)
            
            return network_logs
        except Exception as e:
            logger.debug(f"Error getting network logs: {e}")
            return []
    
    def capture_request(self, method: str, url: str, data: Optional[Dict] = None):
        """Manually capture a request"""
        request_info = {
            'timestamp': time.time(),
            'method': method,
            'url': url,
            'data': data
        }
        
        self.requests.append(request_info)
        logger.network_request(method, url, data)
    
    def capture_response(self, url: str, status_code: int, response_data: Dict):
        """Manually capture a response"""
        response_info = {
            'timestamp': time.time(),
            'url': url,
            'status_code': status_code,
            'data': response_data
        }
        
        self.responses.append(response_info)
        self.last_response = response_info
        logger.network_response(url, status_code, response_data)
        
        return response_info
    
    def wait_for_response(self, timeout: int = 30) -> Optional[Dict]:
        """Wait for a network response and return it"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Get network logs
                logs = self.get_network_logs()
                
                for log in logs:
                    method = log['message']['method']
                    
                    if method == 'Network.responseReceived':
                        response = log['message']['params']['response']
                        url = response['url']
                        status = response['status']
                        
                        # Try to get response body
                        try:
                            request_id = log['message']['params']['requestId']
                            response_body = self.driver.execute_cdp_cmd(
                                'Network.getResponseBody', 
                                {'requestId': request_id}
                            )
                            
                            if response_body.get('body'):
                                try:
                                    # Try to parse as JSON
                                    response_data = json.loads(response_body['body'])
                                except:
                                    # If not JSON, store as text
                                    response_data = {'body': response_body['body']}
                                
                                self.capture_response(url, status, response_data)
                                
                                # Check if this response contains medical center assignment
                                if self._contains_medical_center_assignment(response_data):
                                    return response_data
                        
                        except Exception as e:
                            logger.debug(f"Could not get response body: {e}")
                
                time.sleep(0.5)  # Short delay before checking again
                
            except Exception as e:
                logger.debug(f"Error waiting for response: {e}")
                time.sleep(1)
        
        logger.warning("Response timeout - no response received")
        return None
    
    def _contains_medical_center_assignment(self, response_data: Dict) -> bool:
        """Check if response contains medical center assignment"""
        try:
            # Convert to string for search
            response_str = json.dumps(response_data).lower()
            
            # Look for common patterns indicating medical center assignment
            patterns = [
                'assignedmedicalcenter',
                'medical_center',
                'medicalcenter',
                'clinic',
                'center',
                'hospital',
                'assigned',
                'appointment'
            ]
            
            for pattern in patterns:
                if pattern in response_str:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def extract_medical_center(self, response_data: Dict) -> Optional[str]:
        """Extract medical center name from response"""
        try:
            # Try different possible field names
            possible_fields = [
                'assignedMedicalCenter',
                'medical_center',
                'medicalCenter',
                'clinic_name',
                'center_name',
                'hospital_name',
                'assigned_center',
                'appointment_center'
            ]
            
            # Recursively search through response data
            def search_in_dict(data, fields):
                if isinstance(data, dict):
                    for field in fields:
                        if field in data:
                            return data[field]
                    
                    # Search recursively in nested dictionaries
                    for value in data.values():
                        result = search_in_dict(value, fields)
                        if result:
                            return result
                
                elif isinstance(data, list):
                    for item in data:
                        result = search_in_dict(item, fields)
                        if result:
                            return result
                
                return None
            
            center_name = search_in_dict(response_data, possible_fields)
            
            if center_name:
                logger.medical_center_assigned(str(center_name))
                return str(center_name)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting medical center: {e}")
            return None
    
    def get_last_response(self) -> Optional[Dict]:
        """Get the last captured response"""
        return self.last_response
    
    def clear_logs(self):
        """Clear all captured logs"""
        self.requests = []
        self.responses = []
        self.last_response = None
        logger.debug("Network logs cleared")