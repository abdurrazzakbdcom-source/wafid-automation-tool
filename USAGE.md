# Wafid Medical Appointment Automation Tool - Usage Guide

## Quick Start

### 1. Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Note: You also need Chrome/Chromium browser installed
# ChromeDriver will be managed automatically by Selenium
```

### 2. Basic Usage

#### GUI Mode (Recommended)
```bash
python main.py
```

#### Command Line Mode
```bash
python main.py --target "Green Crescent Clinic" --csv data/demo_candidates.csv
```

### 3. Test Installation
```bash
python test.py
```

## Detailed Usage

### GUI Interface

The GUI provides a user-friendly interface with multiple tabs:

1. **Configuration Tab**
   - Set target medical center name
   - Load candidate data from CSV
   - View current status
   - Control automation (start/stop)

2. **Live Console Tab**
   - Real-time logging output
   - Export logs functionality
   - Auto-scroll toggle

3. **Statistics Tab**
   - Automation statistics
   - Proxy usage stats
   - Performance metrics

4. **Results Tab**
   - Captured payment URLs
   - Export functionality
   - Success history

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --headless          Run browser without UI (background mode)
  --target TEXT       Target medical center name
  --csv FILE          Path to CSV file with candidate data
  --max-retries INT   Maximum retry attempts (default: 100)
  --log-level LEVEL   Logging level: DEBUG, INFO, WARNING, ERROR
```

### CSV Format

The CSV file must contain the following columns:

**Appointment Information:**
- `Appointment_Location` - Location preference
- `Country` - Select Country
- `City` - Select City  
- `Country_Traveling_To` - Destination country

**Candidate Information:**
- `First_Name` - Candidate's first name
- `Last_Name` - Candidate's last name
- `Date_Of_Birth` - Birth date (YYYY-MM-DD format)
- `Nationality` - Nationality
- `Gender` - Gender (Male/Female)
- `Marital_Status` - Marital status
- `Passport_Number` - Passport number
- `Confirm_Passport_Number` - Confirm passport number (same as above)
- `Passport_Issue_Date` - Passport issue date
- `Passport_Issue_Place` - Where passport was issued
- `Passport_Expiry_Date` - Passport expiry date
- `Visa_Type` - Type of visa applying for
- `Email_Address` - Email address
- `Phone` - Phone number
- `National_ID` - National ID number
- `Position_Applied_For` - Job position

Example CSV is provided in `data/demo_candidates.csv`.

## How It Works

### 1. Proxy Management
- Automatically fetches proxy IPs from open-source lists
- Tests each proxy for functionality
- Rotates through working proxies for each attempt
- Real-time logging of proxy success/failure

### 2. Fresh Browser Sessions
- Each attempt starts with a completely clean browser session
- No cookies, cache, or stored data from previous attempts
- Random user agents for better anonymity
- Configurable proxy support

### 3. Form Detection and Filling
- Automatically detects form fields on the booking page
- Maps detected fields to candidate data
- Fills appointment information first (Country, City, Destination)
- Submits and waits for server response

### 4. Medical Center Matching
- Extracts assigned medical center from live server response
- Compares with user-specified target center
- Supports exact match and fuzzy matching
- If no match: clears browser data, switches proxy, retries

### 5. Complete Booking (On Match)
- Fills all candidate information
- Ticks required checkboxes
- Submits final form
- Captures payment page URL
- Saves URL to database/CSV

### 6. Real-time Logging
- All operations logged in real-time
- Separate logs for proxy, browser, network, and decisions
- GUI console shows live progress
- Export logs to CSV/JSON for analysis

## Configuration

The tool can be configured via `config.json`:

```json
{
  "automation": {
    "booking_url": "https://wafid.com/book-appointment",
    "max_retries": 100
  },
  "browser": {
    "headless": false,
    "window_size": "1920,1080"
  },
  "proxy": {
    "min_working_proxies": 10,
    "test_timeout": 10
  }
}
```

## Output Files

- `logs/automation.log` - Main log file
- `logs/network_logs.json` - Network request/response logs
- `data/working_proxies.json` - Validated proxy list
- `data/payment_urls.csv` - Captured payment URLs

## Troubleshooting

### Common Issues

1. **No working proxies**
   - Check internet connection
   - Proxy sources may be temporarily unavailable
   - Try refreshing proxy list manually

2. **Browser fails to start**
   - Ensure Chrome/Chromium is installed
   - Check if ChromeDriver is accessible
   - Try running with `--headless` flag

3. **Form fields not detected**
   - Website structure may have changed
   - Check logs for field detection messages
   - May need to update field mappings

4. **No medical center extracted**
   - Server response format may have changed
   - Check network logs for response structure
   - Verify target center name is correct

### Debug Mode

Run with debug logging for detailed information:
```bash
python main.py --log-level DEBUG
```

## Important Notes

⚠️ **Compliance**: Ensure you comply with the website's terms of service and applicable laws.

⚠️ **Rate Limiting**: The tool includes delays and proxy rotation to avoid overwhelming the server.

⚠️ **Fresh Responses**: The tool ALWAYS uses live server responses for medical center matching - never cached data.

⚠️ **Data Privacy**: Handle candidate data securely and in compliance with privacy regulations.

## Support

For issues or questions:
1. Check the logs in `logs/automation.log`
2. Run `python test.py` to verify installation
3. Review this usage guide
4. Check the GitHub repository for updates

## Examples

### Example 1: Basic GUI Usage
```bash
# Launch GUI
python main.py

# Then in GUI:
# 1. Set target center: "Green Crescent Medical Center"
# 2. Load CSV: data/demo_candidates.csv
# 3. Click "Start Automation"
```

### Example 2: Command Line Automation
```bash
# Run automation with specific parameters
python main.py \
  --target "Al Zahra Medical Center" \
  --csv my_candidates.csv \
  --max-retries 50 \
  --log-level INFO
```

### Example 3: Headless Mode (Server)
```bash
# Run in background without browser UI
python main.py \
  --headless \
  --target "Emirates Medical Center" \
  --csv candidates.csv
```

### Example 4: Proxy Testing Only
```bash
# Test proxy functionality
python -c "
from src.components.proxy_manager import ProxyManager
pm = ProxyManager()
pm.refresh_proxy_list()
print(f'Working proxies: {pm.get_proxy_stats()}')
"
```