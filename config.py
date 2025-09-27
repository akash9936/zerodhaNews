"""
Configuration settings for Zerodha News Analyzer
"""
from datetime import timedelta

# Time Configuration
IST_OFFSET = timedelta(hours=5, minutes=30)

# API Configuration
class GroqConfig:
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
    MAX_CONTEXT_TOKENS = 4000
    MAX_OUTPUT_TOKENS = 1500
    TEMPERATURE = 0.3
    TOP_P = 0.8
    MAX_TOKENS = 800
    TIMEOUT = 60
    MAX_RETRIES = 3

# Scraping Configuration
class ScrapingConfig:
    ZERODHA_PULSE_URL = "https://pulse.zerodha.com/"
    REQUEST_TIMEOUT = 30
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

# Analysis Configuration
class AnalysisConfig:
    BATCH_SIZE = 15
    RATE_LIMIT_DELAY = 1  # seconds between batches
    RATE_LIMIT_RETRY_DELAY = 15  # seconds on rate limit hit

    # Sector Keywords for categorization
    SECTOR_KEYWORDS = {
        'banking': ['bank', 'icici', 'hdfc', 'sbi', 'axis', 'kotak', 'npa', 'credit'],
        'technology': ['tech', 'it', 'infosys', 'tcs', 'wipro', 'software', 'digital'],
        'pharma': ['pharma', 'drug', 'medicine', 'fda', 'reddy', 'sun pharma', 'cipla'],
        'power': ['power', 'ntpc', 'renewable', 'energy', 'coal', 'electricity'],
        'auto': ['auto', 'car', 'motor', 'tata motors', 'hyundai', 'maruti'],
        'fmcg': ['fmcg', 'consumer', 'itc', 'hindustan unilever', 'nestle'],
        'metals': ['metal', 'steel', 'iron', 'copper', 'aluminum', 'tata steel'],
        'oil_gas': ['oil', 'gas', 'petroleum', 'reliance', 'ongc', 'crude'],
        'realty': ['real estate', 'property', 'construction', 'housing'],
        'aviation': ['aviation', 'airline', 'aircraft', 'airport', 'indigo', 'air india']
    }

    # High impact keywords for news prioritization
    HIGH_IMPACT_KEYWORDS = [
        # Corporate Actions
        'results', 'earnings', 'profit', 'loss', 'merger', 'acquisition',
        'ipo', 'dividend', 'buyback', 'split', 'delisting', 'rating',
        'upgrade', 'downgrade', 'target', 'recommendation',

        # Financial Metrics
        'revenue', 'growth', 'margin', 'ebitda', 'pat', 'eps',
        'guidance', 'forecast', 'outlook', 'projection',

        # Corporate Events
        'launch', 'expansion', 'investment', 'capex', 'order', 'contract',
        'deal', 'partnership', 'collaboration', 'venture',

        # Market Actions
        'circuit', 'upper circuit', 'lower circuit', 'breakout', 'breakdown',
        'surge', 'plunge', 'rally', 'correction', 'volatility',

        # Analyst Actions
        'initiate', 'maintain', 'retain', 'revise', 'cut', 'raise',
        'bullish', 'bearish', 'neutral', 'outperform', 'underperform'
    ]

    # Market moving events keywords
    MARKET_MOVER_KEYWORDS = [
        # Existing terms
        'fii', 'dii', 'rbi', 'sebi', 'government', 'policy', 'tax',
        'interest rate', 'inflation', 'gdp', 'budget',

        # Market Structure
        'sensex', 'nifty', 'bullish', 'bearish', 'correction', 'rally',
        'volatility', 'consolidation',

        # Technical Analysis
        'sma', 'ema', 'resistance', 'support', 'breakout', 'breakdown',
        'volume', 'technical', 'pattern',

        # Corporate Actions
        'merger', 'acquisition', 'm&a', 'dividend', 'buyback',
        'earnings', 'results', 'quarterly', 'guidance', 'outlook',

        # Sectors
        'banking', 'finance', 'it', 'auto', 'pharma', 'realty',
        'infrastructure', 'cement', 'energy', 'power', 'oil',
        'defense', 'aerospace',

        # Global Markets
        'futures', 'dow', 'nasdaq', 'asian', 'european',
        'tariff', 'trade', 'commodity', 'gold', 'crude'
    ]

# Telegram Configuration
class TelegramConfig:
    MAX_MESSAGE_LENGTH = 4000
    PARSE_MODE = 'HTML'

# File Configuration
class FileConfig:
    DATA_DIR = 'data'
    REPORT_FILENAME_FORMAT = "zerodha_news_report_{timestamp}.txt"
    NEWS_FILENAME_FORMAT = "pulse_news_{timestamp}.json"
    TIMESTAMP_FORMAT = '%Y-%m-%d_%H-%M-%S'
    JSON_TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'
    ENCODING = 'utf-8'

# Logging Configuration
class LoggingConfig:
    LEVEL = 'INFO'
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'