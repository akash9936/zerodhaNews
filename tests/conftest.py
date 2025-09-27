"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_news_data():
    """Sample news data for testing"""
    return [
        {
            'headline': 'HDFC Bank Q4 results: Net profit rises 20% to Rs 15,976 crore',
            'description': 'The bank reported strong growth in deposits and advances',
            'source': 'Economic Times',
            'time': 'Today, 10:30 AM',
            'url': 'https://example.com/hdfc-results'
        },
        {
            'headline': 'Infosys announces dividend of Rs 18 per share',
            'description': 'The IT giant also reported revenue growth of 12%',
            'source': 'Business Standard',
            'time': 'Yesterday, 2:15 PM',
            'url': 'https://example.com/infosys-dividend'
        },
        {
            'headline': 'RBI keeps repo rate unchanged at 6.5%',
            'description': 'Central bank maintains accommodative stance',
            'source': 'Reuters',
            'time': '26 May 2025, 11:45 AM',
            'url': 'https://example.com/rbi-policy'
        }
    ]


@pytest.fixture
def sample_analysis_results():
    """Sample analysis results for testing"""
    return {
        'total_news_items': 50,
        'sector_summary': {
            'banking': 10,
            'technology': 8,
            'pharma': 5,
            'general': 27
        },
        'final_report': """**Key Sector Trends** 🌍📈
- Banking: HDFC Bank reports strong Q4 results with 20% profit growth
- Technology: Infosys announces dividend, showing sector strength

**Buy/Sell Opportunities** 💰🔍
- Buy: HDFC Bank on strong fundamentals
- Sell/Avoid: None identified in current batch

**Macro Implications** 🏦📉
- RBI maintains status quo on interest rates
- Banking sector showing resilience

**Corporate Actions** 🗓️🏢
- HDFC Bank Q4 results released
- Infosys dividend announcement""",
        'api_calls_used': 4,
        'analysis_timestamp': datetime.now().isoformat()
    }


@pytest.fixture
def mock_groq_response():
    """Mock Groq API response"""
    return {
        'choices': [{
            'message': {
                'content': """**Key Sector Trends** 🌍📈
- Banking: Strong quarterly results
- Technology: Dividend announcements

**Buy/Sell Opportunities** 💰🔍
- Buy: HDFC Bank
- Sell/Avoid: None

**Macro Implications** 🏦📉
- Stable interest rate environment

**Corporate Actions** 🗓️🏢
- Q4 earnings season continues"""
            }
        }]
    }


@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot for testing"""
    mock_bot = Mock()
    mock_bot.send_message.return_value = True
    return mock_bot


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary data directory for testing"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return str(data_dir)


@pytest.fixture
def mock_requests_response():
    """Mock requests response for web scraping"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = """
    <html>
        <body>
            <ul id="news">
                <li class="box item">
                    <h2 class="title"><a href="/test-url">Test Headline</a></h2>
                    <div class="desc">Test description</div>
                    <div class="date" title="Today, 10:30 AM">Today, 10:30 AM</div>
                    <div class="feed">Test Source</div>
                </li>
            </ul>
        </body>
    </html>
    """
    return mock_response