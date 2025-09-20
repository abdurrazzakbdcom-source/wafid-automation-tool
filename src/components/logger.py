import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import threading


class AutomationLogger:
    """Comprehensive logging system for the automation tool"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, "automation.log")
        self.network_log_file = os.path.join(log_dir, "network_logs.json")
        self.lock = threading.Lock()
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup file logger
        self.setup_file_logger()
        
        # Initialize network logs
        self.network_logs = []
        
        # GUI console callback (will be set by GUI)
        self.gui_console_callback = None
    
    def setup_file_logger(self):
        """Setup file logging configuration"""
        self.logger = logging.getLogger('automation')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def set_gui_callback(self, callback):
        """Set GUI console callback for real-time display"""
        self.gui_console_callback = callback
    
    def _log_to_gui(self, message: str):
        """Send log message to GUI console if callback is set"""
        if self.gui_console_callback:
            try:
                self.gui_console_callback(message)
            except Exception as e:
                print(f"GUI callback error: {e}")
    
    def info(self, message: str):
        """Log info message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] INFO: {message}"
        
        with self.lock:
            self.logger.info(message)
            self._log_to_gui(formatted_msg)
    
    def warning(self, message: str):
        """Log warning message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] WARNING: {message}"
        
        with self.lock:
            self.logger.warning(message)
            self._log_to_gui(formatted_msg)
    
    def error(self, message: str):
        """Log error message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] ERROR: {message}"
        
        with self.lock:
            self.logger.error(message)
            self._log_to_gui(formatted_msg)
    
    def debug(self, message: str):
        """Log debug message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] DEBUG: {message}"
        
        with self.lock:
            self.logger.debug(message)
            # Debug messages only go to file, not GUI console
    
    def proxy_success(self, proxy: str, response_time: float):
        """Log proxy success"""
        self.info(f"Proxy {proxy} - SUCCESS (Response time: {response_time:.2f}s)")
    
    def proxy_failure(self, proxy: str, error: str):
        """Log proxy failure"""
        self.warning(f"Proxy {proxy} - FAILED ({error})")
    
    def browser_fresh_session(self):
        """Log fresh browser session start"""
        self.info("Started fresh browser session (cookies cleared, storage reset)")
    
    def dom_field_detected(self, field_name: str, selector: str):
        """Log DOM field detection"""
        self.info(f"Detected field: {field_name} → {selector}")
    
    def network_request(self, method: str, url: str, data: Optional[Dict] = None):
        """Log network request"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'request',
            'method': method,
            'url': url,
            'data': data
        }
        
        with self.lock:
            self.network_logs.append(log_entry)
            self._save_network_logs()
        
        self.debug(f"Network Request: {method} {url}")
    
    def network_response(self, url: str, status_code: int, response_data: Dict):
        """Log network response"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'response',
            'url': url,
            'status_code': status_code,
            'data': response_data
        }
        
        with self.lock:
            self.network_logs.append(log_entry)
            self._save_network_logs()
        
        self.info(f"Response received: Status {status_code}")
        
        # Check for medical center assignment
        if 'assignedMedicalCenter' in str(response_data):
            self.info(f"Medical center assignment detected in response")
    
    def medical_center_assigned(self, center_name: str):
        """Log medical center assignment"""
        self.info(f"Response received: {{assignedMedicalCenter: \"{center_name}\"}}")
    
    def medical_center_match(self, assigned: str, target: str):
        """Log medical center match"""
        self.info(f"Match found! Center = {assigned}")
    
    def medical_center_mismatch(self, assigned: str, target: str):
        """Log medical center mismatch"""
        self.warning(f"Assigned center {assigned} ≠ Target center {target}")
    
    def payment_url_captured(self, url: str):
        """Log payment URL capture"""
        self.info(f"Payment URL captured: {url}")
    
    def form_field_filled(self, field_name: str, value: str):
        """Log form field filling"""
        # Mask sensitive data
        if any(sensitive in field_name.lower() for sensitive in ['password', 'passport', 'id']):
            value = '*' * len(str(value))
        
        self.debug(f"Filled field: {field_name} = {value}")
    
    def automation_started(self, target_center: str):
        """Log automation start"""
        self.info(f"Automation started - Target medical center: {target_center}")
    
    def automation_stopped(self):
        """Log automation stop"""
        self.info("Automation stopped by user")
    
    def _save_network_logs(self):
        """Save network logs to JSON file"""
        try:
            with open(self.network_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.network_logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save network logs: {e}")
    
    def export_logs_csv(self, filename: str) -> bool:
        """Export logs to CSV format"""
        try:
            import pandas as pd
            
            # Parse log file
            log_entries = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split('] ', 2)
                        if len(parts) >= 3:
                            timestamp = parts[0][1:]  # Remove leading [
                            level = parts[1]
                            message = parts[2]
                            log_entries.append({
                                'timestamp': timestamp,
                                'level': level,
                                'message': message
                            })
            
            df = pd.DataFrame(log_entries)
            df.to_csv(filename, index=False)
            self.info(f"Logs exported to {filename}")
            return True
            
        except Exception as e:
            self.error(f"Failed to export logs to CSV: {e}")
            return False
    
    def export_network_logs_json(self, filename: str) -> bool:
        """Export network logs to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.network_logs, f, indent=2, ensure_ascii=False)
            self.info(f"Network logs exported to {filename}")
            return True
        except Exception as e:
            self.error(f"Failed to export network logs: {e}")
            return False
    
    def clear_logs(self):
        """Clear all logs"""
        with self.lock:
            # Clear file logs
            open(self.log_file, 'w').close()
            
            # Clear network logs
            self.network_logs = []
            open(self.network_log_file, 'w').close()
            
            self.info("All logs cleared")


# Global logger instance
logger = AutomationLogger()