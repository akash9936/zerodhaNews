"""
Unit tests for news_scraper module
"""
import pytest
import json
import os
from unittest.mock import patch, Mock, mock_open
from news_scraper import ZerodhaPulseScraper


class TestZerodhaPulseScraper:

    def test_init(self):
        """Test scraper initialization"""
        scraper = ZerodhaPulseScraper()
        assert scraper.url == "https://pulse.zerodha.com/"
        assert scraper.timeout == 30
        assert 'User-Agent' in scraper.headers

    @patch('news_scraper.requests.get')
    def test_scrape_news_success(self, mock_get, mock_requests_response):
        """Test successful news scraping"""
        mock_get.return_value = mock_requests_response
        scraper = ZerodhaPulseScraper()

        result = scraper.scrape_news()

        assert result is not None
        assert len(result) == 1
        assert result[0]['headline'] == 'Test Headline'
        assert result[0]['description'] == 'Test description'
        assert result[0]['time'] == 'Today, 10:30 AM'
        assert result[0]['source'] == 'Test Source'
        assert result[0]['url'] == '/test-url'

    @patch('news_scraper.requests.get')
    def test_scrape_news_network_error(self, mock_get):
        """Test scraping with network error"""
        mock_get.side_effect = Exception("Network error")
        scraper = ZerodhaPulseScraper()

        result = scraper.scrape_news()

        assert result is None

    @patch('news_scraper.requests.get')
    def test_scrape_news_no_news_list(self, mock_get):
        """Test scraping when news list is not found"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No news list here</body></html>"
        mock_get.return_value = mock_response

        scraper = ZerodhaPulseScraper()
        result = scraper.scrape_news()

        assert result is None

    @patch('news_scraper.requests.get')
    def test_scrape_news_empty_list(self, mock_get):
        """Test scraping with empty news list"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body><ul id="news"></ul></body></html>'
        mock_get.return_value = mock_response

        scraper = ZerodhaPulseScraper()
        result = scraper.scrape_news()

        assert result is None

    @patch('news_scraper.requests.get')
    def test_scrape_news_malformed_html(self, mock_get):
        """Test scraping with malformed HTML"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html><body>
            <ul id="news">
                <li class="box item">
                    <!-- Missing required elements -->
                </li>
            </ul>
        </body></html>
        """
        mock_get.return_value = mock_response

        scraper = ZerodhaPulseScraper()
        result = scraper.scrape_news()

        assert result is None  # Should return None when no valid items found

    def test_extract_news_item_valid(self):
        """Test extracting valid news item"""
        from bs4 import BeautifulSoup

        html = """
        <li class="box item">
            <h2 class="title"><a href="/test">Test Headline</a></h2>
            <div class="desc">Test description</div>
            <div class="date" title="Today, 10:30 AM">Today</div>
            <div class="feed">Test Source —</div>
        </li>
        """
        soup = BeautifulSoup(html, 'html.parser')
        item = soup.find('li')

        scraper = ZerodhaPulseScraper()
        result = scraper._extract_news_item(item, 1)

        assert result is not None
        assert result['headline'] == 'Test Headline'
        assert result['description'] == 'Test description'
        assert result['time'] == 'Today, 10:30 AM'
        assert result['source'] == 'Test Source'
        assert result['url'] == '/test'

    def test_extract_news_item_missing_headline(self):
        """Test extracting news item with missing headline"""
        from bs4 import BeautifulSoup

        html = '<li class="box item"><div class="desc">Description only</div></li>'
        soup = BeautifulSoup(html, 'html.parser')
        item = soup.find('li')

        scraper = ZerodhaPulseScraper()
        result = scraper._extract_news_item(item, 1)

        assert result is None

    def test_extract_news_item_empty_headline(self):
        """Test extracting news item with empty headline"""
        from bs4 import BeautifulSoup

        html = """
        <li class="box item">
            <h2 class="title"><a href="/test"></a></h2>
        </li>
        """
        soup = BeautifulSoup(html, 'html.parser')
        item = soup.find('li')

        scraper = ZerodhaPulseScraper()
        result = scraper._extract_news_item(item, 1)

        assert result is None

    def test_extract_news_item_minimal_data(self):
        """Test extracting news item with minimal data"""
        from bs4 import BeautifulSoup

        html = """
        <li class="box item">
            <h2 class="title"><a href="">Minimal Headline</a></h2>
        </li>
        """
        soup = BeautifulSoup(html, 'html.parser')
        item = soup.find('li')

        scraper = ZerodhaPulseScraper()
        result = scraper._extract_news_item(item, 1)

        assert result is not None
        assert result['headline'] == 'Minimal Headline'
        assert result['description'] == ''
        assert result['time'] == 'Unknown time'
        assert result['source'] == 'Unknown source'
        assert result['url'] == ''

    @patch('news_scraper.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('news_scraper.format_json_timestamp')
    def test_save_news_data_success(self, mock_timestamp, mock_file, mock_makedirs):
        """Test saving news data successfully"""
        mock_timestamp.return_value = "20250101_120000"
        news_items = [{'headline': 'Test', 'description': 'Test desc'}]

        scraper = ZerodhaPulseScraper()
        result = scraper.save_news_data(news_items)

        assert result == 'data/pulse_news_20250101_120000.json'
        mock_makedirs.assert_called_once_with('data', exist_ok=True)
        mock_file.assert_called_once()

    @patch('news_scraper.os.makedirs')
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_save_news_data_error(self, mock_file, mock_makedirs):
        """Test saving news data with file error"""
        news_items = [{'headline': 'Test'}]

        scraper = ZerodhaPulseScraper()
        result = scraper.save_news_data(news_items)

        assert result is None

    @patch('news_scraper.requests.get')
    def test_scrape_news_http_error(self, mock_get):
        """Test scraping with HTTP error"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        mock_get.return_value = mock_response

        scraper = ZerodhaPulseScraper()
        result = scraper.scrape_news()

        assert result is None

    @patch('news_scraper.requests.get')
    def test_scrape_news_timeout(self, mock_get):
        """Test scraping with timeout"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        scraper = ZerodhaPulseScraper()
        result = scraper.scrape_news()

        assert result is None