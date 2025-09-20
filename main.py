#!/usr/bin/env python3
"""
Wafid Medical Appointment Automation Tool
Main application entry point
"""

import sys
import os
import argparse
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from gui.main_window import WafidAutomationGUI
from components.logger import logger


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="Wafid Medical Appointment Automation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Launch GUI interface
  python main.py --headless         # Launch in headless mode (no browser UI)
  python main.py --target "Clinic"  # Set target medical center
  python main.py --csv data.csv     # Load specific CSV file

Features:
  - Proxy management with automatic testing and rotation
  - Fresh browser sessions for each attempt
  - Real-time logging and monitoring
  - Medical center matching with automatic retry
  - Payment URL capture and export
  - Comprehensive GUI with live console

For more information, see README.md
        """
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no GUI)"
    )
    
    parser.add_argument(
        "--target",
        type=str,
        help="Target medical center name"
    )
    
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to CSV file with candidate data"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=100,
        help="Maximum number of retry attempts (default: 100)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    import logging
    logging.getLogger('automation').setLevel(getattr(logging, args.log_level))
    
    logger.info("Starting Wafid Medical Appointment Automation Tool")
    logger.info(f"Arguments: {vars(args)}")
    
    try:
        # Ensure required directories exist
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Check if running in CLI mode (with specific arguments)
        if args.target and args.csv:
            # CLI mode - run automation directly
            run_cli_automation(args)
        else:
            # GUI mode - launch interface
            logger.info("Launching GUI interface...")
            app = WafidAutomationGUI()
            
            # Pre-configure if arguments provided
            if args.target:
                app.target_center = args.target
                app.center_entry.insert(0, args.target)
            
            if args.csv:
                app.csv_file_path = args.csv
                app.csv_path_var.set(args.csv)
            
            app.run()
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


def run_cli_automation(args):
    """Run automation in CLI mode"""
    from components.automation_engine import AutomationEngine
    
    logger.info("Running in CLI mode")
    
    # Initialize automation engine
    engine = AutomationEngine()
    engine.max_retries = args.max_retries
    
    # Configure browser headless mode
    engine.browser.headless = args.headless
    
    # Set target medical center
    engine.set_target_medical_center(args.target)
    
    # Load candidate data
    if not engine.load_candidate_data(args.csv):
        logger.error("Failed to load candidate data")
        sys.exit(1)
    
    # Run automation
    logger.info("Starting automation...")
    success = engine.start_automation()
    
    if success:
        logger.info("Automation completed successfully!")
        sys.exit(0)
    else:
        logger.error("Automation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()