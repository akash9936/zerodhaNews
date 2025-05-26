from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import json
from datetime import datetime, date, timedelta
import time
import sys

# ===== CONFIGURABLE PARAMETERS =====
# Set your desired start date and time here (in IST)
START_DATE = "27 May 2025"  # Format: "DD MMM YYYY"
START_TIME = "12:00 AM"     # Format: "HH:MM AM/PM"
# ==================================

def parse_start_datetime():
    """
    Parse the configured start date and time into a datetime object
    Input time is already in IST, so no need to add offset
    """
    try:
        # Combine date and time strings
        datetime_str = f"{START_TIME}, {START_DATE}"
        # Parse into datetime object (already in IST)
        start_datetime = datetime.strptime(datetime_str, "%I:%M %p, %d %b %Y")
        return start_datetime
    except ValueError as e:
        print(f"Error parsing start date/time: {e}")
        print("Please check the format of START_DATE and START_TIME")
        sys.exit(1)

def get_ist_time():
    """
    Get current time in IST (UTC+5:30)
    """
    # Get UTC time and add 5 hours and 30 minutes for IST
    utc_now = datetime.utcnow()
    ist_time = utc_now + timedelta(hours=5, minutes=30)
    return ist_time

def is_within_time_range(time_text):
    """
    Check if the news item is within the configured time range
    """
    # Get start time and current time in IST
    start_time_ist = parse_start_datetime()  # Already in IST
    current_time_ist = get_ist_time()
    
    # Try to parse different date formats
    try:
        # Handle "X hours/minutes ago" format
        if 'ago' in time_text.lower():
            # For "ago" format, we'll consider it within range
            # as it's recent enough to be after our start time
            return True
            
        # Handle "Today at HH:MM" format
        if 'today' in time_text.lower():
            # For "today" format, we'll check if it's after our start time
            return current_time_ist >= start_time_ist
            
        # Handle IST format (e.g., "12:27 AM, 27 May 2025")
        try:
            # Parse the date string (already in IST)
            news_datetime = datetime.strptime(time_text, "%I:%M %p, %d %b %Y")
            
            # Check if news time is between start time and current time
            return start_time_ist <= news_datetime <= current_time_ist
            
        except ValueError as e:
            print(f"Could not parse date format: {time_text}")
            return False
            
    except Exception as e:
        print(f"Error parsing date '{time_text}': {e}")
        return False
    
    return False

def scrape_pulse_zerodha():
    """
    Script to scrape Zerodha Pulse website using Chrome in headless mode.
    Fetches news from configured start time until current time.
    """
    print("Starting Zerodha Pulse scraper using Chrome in headless mode...")
    
    # Get time range for logging
    start_time_ist = parse_start_datetime()
    current_time_ist = get_ist_time()
    print(f"Fetching news from: {start_time_ist.strftime('%I:%M %p, %d %b %Y')}")
    print(f"Until current time: {current_time_ist.strftime('%I:%M %p, %d %b %Y')}")
    
    # URL of the website
    url = "https://pulse.zerodha.com/"
    
    # Set up Chrome options for headless mode
    chrome_options = ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        # Create Chrome browser instance
        print("Initializing Chrome WebDriver in headless mode...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the page
        print("Loading Zerodha Pulse website...")
        driver.get(url)
        
        # Wait for the news list to load
        print("Waiting for news list to load...")
        wait = WebDriverWait(driver, 15)
        
        # Wait for the news list to be present
        news_list = wait.until(EC.presence_of_element_located((By.ID, "news")))
        print("Found news list")
        
        # Wait for news items to be present
        news_items = []
        try:
            # Find all news items (li elements with class 'box item')
            items = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#news li.box.item")))
            print(f"Found {len(items)} total news items")
            
            # Process each news item
            for i, item in enumerate(items, 1):
                try:
                    # Extract headline from h2.title a
                    headline_element = item.find_element(By.CSS_SELECTOR, "h2.title a")
                    headline = headline_element.text.strip()
                    
                    # Extract description
                    try:
                        desc_element = item.find_element(By.CLASS_NAME, "desc")
                        description = desc_element.text.strip()
                    except:
                        description = ""
                    
                    # Extract date and source
                    try:
                        date_element = item.find_element(By.CLASS_NAME, "date")
                        time_text = date_element.get_attribute("title")  # Get the full date from title
                        if not time_text:
                            time_text = date_element.text.strip()
                    except:
                        time_text = "Unknown time"
                        
                    # Skip if not within time range
                    if not is_within_time_range(time_text):
                        continue
                        
                    try:
                        source_element = item.find_element(By.CLASS_NAME, "feed")
                        source = source_element.text.strip().replace("—", "").strip()
                    except:
                        source = "Unknown source"
                    
                    # Create news item dictionary
                    news_item = {
                        'headline': headline,
                        'description': description,
                        'source': source,
                        'time': time_text,
                        'url': headline_element.get_attribute("href")
                    }
                    
                    news_items.append(news_item)
                    print(f"Article {len(news_items)}: {headline[:50]}...")
                    
                except Exception as e:
                    print(f"Error processing article {i}: {e}")
                    continue
            
            # Save to JSON file with time range in filename
            start_str = start_time_ist.strftime("%Y%m%d_%H%M")
            end_str = current_time_ist.strftime("%Y%m%d_%H%M")
            filename = f"pulse_news_{start_str}_to_{end_str}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(news_items, f, indent=4, ensure_ascii=False)
            
            print(f"\nSuccessfully scraped {len(news_items)} news items")
            print(f"Data saved to {filename}")
            
            return news_items
            
        except TimeoutException as e:
            print("\nTimeout waiting for news items to load.")
            print("Current page source preview:")
            print(driver.page_source[:500] + "...")
            raise e
        
    except WebDriverException as e:
        print("\nChrome WebDriver Error:")
        print("Please make sure you have:")
        print("1. Chrome browser installed")
        print("2. ChromeDriver installed and in your PATH")
        print(f"\nTechnical error: {e}")
        return None
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        if 'driver' in locals():
            print("\nPage source preview:")
            print(driver.page_source[:1000] + "...")
        return None
    finally:
        # Always close the browser
        print("\nClosing browser...")
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    try:
        # Run the scraper
        scrape_pulse_zerodha()
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting...")
        sys.exit(0)