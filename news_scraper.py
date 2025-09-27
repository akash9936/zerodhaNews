"""
News scraping functionality for Zerodha Pulse
"""
import os
import json
import logging
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from config import ScrapingConfig, FileConfig
from utils.time_utils import format_json_timestamp

logger = logging.getLogger(__name__)


class ZerodhaPulseScraper:
    """Scraper for Zerodha Pulse news website"""

    def __init__(self):
        self.url = ScrapingConfig.ZERODHA_PULSE_URL
        self.headers = ScrapingConfig.HEADERS
        self.timeout = ScrapingConfig.REQUEST_TIMEOUT

    def scrape_news(self) -> Optional[List[Dict]]:
        """
        Scrape news from Zerodha Pulse website using requests and BeautifulSoup

        Returns:
            List of news items or None if scraping fails
        """
        logger.info("Starting Zerodha Pulse scraper...")

        try:
            logger.info("Fetching news from Zerodha Pulse...")
            response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the news list
            news_list = soup.find('ul', id='news')

            if not news_list:
                logger.warning("News list not found in the page")
                return None

            items = news_list.find_all('li', class_='box item')
            logger.info(f"Found {len(items)} total news items")

            news_items = []
            logger.info(f"Processing latest {len(items)} news items")

            for idx, item in enumerate(items, 1):
                try:
                    news_item = self._extract_news_item(item, idx)
                    if news_item:
                        news_items.append(news_item)
                        logger.debug(f"Article {len(news_items)}: {news_item['headline'][:50]}...")

                except Exception as e:
                    logger.error(f"Error processing article {idx}: {str(e)}")
                    continue

            if not news_items:
                logger.warning("No valid news items were found")
                return None

            logger.info(f"Successfully scraped {len(news_items)} latest news items")
            return news_items

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error occurred: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return None

    def _extract_news_item(self, item, idx: int) -> Optional[Dict]:
        """Extract news item data from HTML element"""
        # Extract headline with safe navigation
        headline_elem = item.select_one('h2.title a')
        if not headline_elem:
            logger.debug(f"Skipping item {idx}: No headline found")
            return None

        headline = headline_elem.get_text(strip=True)
        if not headline:
            logger.debug(f"Skipping item {idx}: Empty headline")
            return None

        # Extract description with safe navigation
        desc_elem = item.select_one('div.desc')
        description = desc_elem.get_text(strip=True) if desc_elem else ""

        # Extract date with safe navigation
        date_elem = item.select_one('div.date')
        time_text = ""
        if date_elem:
            time_text = date_elem.get('title', '') or date_elem.get_text(strip=True)
        if not time_text:
            time_text = "Unknown time"

        # Extract source with safe navigation
        source_elem = item.select_one('div.feed')
        source = "Unknown source"
        if source_elem:
            source = source_elem.get_text(strip=True).replace("—", "").strip()

        # Get URL with safe navigation
        url = headline_elem.get('href', '')

        # Create news item
        return {
            'headline': headline,
            'description': description,
            'source': source,
            'time': time_text,
            'url': url
        }

    def save_news_data(self, news_items: List[Dict]) -> Optional[str]:
        """Save news data to JSON file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(FileConfig.DATA_DIR, exist_ok=True)

            # Generate filename with timestamp
            timestamp = format_json_timestamp()
            filename = os.path.join(
                FileConfig.DATA_DIR,
                FileConfig.NEWS_FILENAME_FORMAT.format(timestamp=timestamp)
            )

            # Save to JSON file
            with open(filename, 'w', encoding=FileConfig.ENCODING) as f:
                json.dump(news_items, f, indent=4, ensure_ascii=False)

            logger.info(f"Data saved to {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error saving news data: {str(e)}")
            return None