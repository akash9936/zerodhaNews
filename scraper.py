from selenium import webdriver
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import json
from datetime import datetime
import time
import sys

def check_safari_setup():
    """
    Check if Safari is properly set up for automation
    """
    print("Checking Safari setup...")
    print("\nPlease ensure you have:")
    print("1. Enabled the Develop menu in Safari (Safari > Settings > Advanced > Show Develop menu)")
    print("2. Enabled Remote Automation (Develop > Allow Remote Automation)")
    print("3. Trusted the WebDriver in System Preferences > Security & Privacy")
    print("\nPress Enter to continue or Ctrl+C to exit...")
    input()

def scrape_pulse_zerodha():
    """
    Simple script to scrape Zerodha Pulse website using Safari on macOS.
    Safari WebDriver is built into macOS and doesn't have the security issues of ChromeDriver.
    """
    print("Starting Zerodha Pulse scraper using Safari...")
    
    # Check Safari setup first
    check_safari_setup()
    
    # URL of the website
    url = "https://pulse.zerodha.com/"
    
    # Set up Safari options
    safari_options = SafariOptions()
    
    try:
        # Create Safari browser instance - Safari WebDriver is built into macOS
        print("Initializing Safari WebDriver...")
        driver = webdriver.Safari(options=safari_options)
        
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
            print(f"Found {len(items)} news items")
            
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
                    print(f"Article {i}: {headline[:50]}...")
                    
                except Exception as e:
                    print(f"Error processing article {i}: {e}")
                    continue
            
            # Save to JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pulse_news_{timestamp}.json"
            
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
        print("\nSafari WebDriver Error:")
        print("Please make sure you have:")
        print("1. Enabled the Develop menu in Safari (Safari > Settings > Advanced > Show Develop menu)")
        print("2. Enabled Remote Automation (Develop > Allow Remote Automation)")
        print("3. Trusted the WebDriver in System Preferences > Security & Privacy")
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