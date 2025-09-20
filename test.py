#!/usr/bin/env python3
"""
Test script for Wafid Automation Tool
Validates basic functionality without running full automation
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from components.logger import logger
        print("✓ Logger imported successfully")
        
        from components.proxy_manager import ProxyManager
        print("✓ Proxy Manager imported successfully")
        
        from components.browser_automation import BrowserAutomation
        print("✓ Browser Automation imported successfully")
        
        from components.network_monitor import NetworkMonitor
        print("✓ Network Monitor imported successfully")
        
        from components.form_handler import FormHandler
        print("✓ Form Handler imported successfully")
        
        from components.automation_engine import AutomationEngine
        print("✓ Automation Engine imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_logger():
    """Test logging functionality"""
    print("\nTesting logger...")
    
    try:
        from components.logger import logger
        
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        print("✓ Logger test completed")
        return True
        
    except Exception as e:
        print(f"✗ Logger test failed: {e}")
        return False

def test_proxy_manager():
    """Test proxy manager initialization"""
    print("\nTesting proxy manager...")
    
    try:
        from components.proxy_manager import ProxyManager
        
        pm = ProxyManager()
        stats = pm.get_proxy_stats()
        
        print(f"✓ Proxy Manager initialized - {stats['total_working']} working proxies")
        return True
        
    except Exception as e:
        print(f"✗ Proxy Manager test failed: {e}")
        return False

def test_automation_engine():
    """Test automation engine initialization"""
    print("\nTesting automation engine...")
    
    try:
        from components.automation_engine import AutomationEngine
        
        engine = AutomationEngine()
        engine.set_target_medical_center("Test Medical Center")
        
        stats = engine.get_statistics()
        print(f"✓ Automation Engine initialized - Target: {stats['target_center']}")
        return True
        
    except Exception as e:
        print(f"✗ Automation Engine test failed: {e}")
        return False

def test_csv_loading():
    """Test CSV loading functionality"""
    print("\nTesting CSV loading...")
    
    try:
        from components.automation_engine import AutomationEngine
        
        engine = AutomationEngine()
        csv_file = "data/demo_candidates.csv"
        
        if os.path.exists(csv_file):
            success = engine.load_candidate_data(csv_file)
            if success:
                stats = engine.get_statistics()
                print(f"✓ CSV loaded successfully - Candidate: {stats['candidate_summary']}")
                return True
            else:
                print("✗ CSV loading failed")
                return False
        else:
            print(f"✗ CSV file not found: {csv_file}")
            return False
            
    except Exception as e:
        print(f"✗ CSV loading test failed: {e}")
        return False

def test_gui_import():
    """Test GUI import (without launching)"""
    print("\nTesting GUI import...")
    
    try:
        # This will test if tkinter is available
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        
        from gui.main_window import WafidAutomationGUI
        print("✓ GUI components imported successfully")
        return True
        
    except ImportError as e:
        print(f"✗ GUI import failed (tkinter not available): {e}")
        return False
    except Exception as e:
        print(f"✗ GUI test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Wafid Automation Tool - Test Suite ===\n")
    
    # Ensure directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    tests = [
        test_imports,
        test_logger,
        test_proxy_manager,
        test_automation_engine,
        test_csv_loading,
        test_gui_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The automation tool is ready to use.")
        print("\nTo run the tool:")
        print("  python main.py                    # GUI mode")
        print("  python main.py --help             # See all options")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)