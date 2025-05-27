import os
import json
import time
import logging
import requests
import re
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from telegram_bot import TelegramBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IST is UTC+5:30
IST_OFFSET = timedelta(hours=5, minutes=30)

def get_ist_time() -> datetime:
    """Get current time in IST."""
    return datetime.utcnow() + IST_OFFSET

def get_groq_token() -> Optional[str]:
    """Get Groq API token with validation."""
    load_dotenv()
    token = os.getenv("GROQ_API_KEY")

    if not token or not token.startswith("gsk_"):
        logger.warning("Groq API token not found or invalid.")
        logger.info("Get a token from: https://console.groq.com/keys")
        token = input("Enter your Groq API token (starts with 'gsk_'): ").strip()
        
        if token and token.startswith("gsk_"):
            # Save token to .env file
            with open(".env", "a") as f:
                f.write(f"\nGROQ_API_KEY={token}")
            logger.info("Token saved to .env file")
        else:
            logger.error("Invalid token format. Token should start with 'gsk_'")
            return None
    
    return token

def check_safari_setup():
    """Check if Safari is properly set up for automation"""
    print("Checking Safari setup...")
    print("\nPlease ensure you have:")
    print("1. Enabled the Develop menu in Safari (Safari > Settings > Advanced > Show Develop menu)")
    print("2. Enabled Remote Automation (Develop > Allow Remote Automation)")
    print("3. Trusted the WebDriver in System Preferences > Security & Privacy")
    print("\nPress Enter to continue or Ctrl+C to exit...")
    input()

def parse_news_time(time_text: str) -> datetime:
    """Parse news time text into datetime object in IST."""
    try:
        # Handle unknown or empty time values
        if not time_text or time_text.lower() == 'unknown time':
            # Return current time for unknown times
            return get_ist_time()
            
        # Handle different time formats
        time_text = time_text.lower().strip()
        now = get_ist_time()
        
        if 'today' in time_text:
            # Format: "Today, 10:30 AM"
            time_str = time_text.replace('today,', '').strip()
            time_obj = datetime.strptime(time_str, '%I:%M %p')
            return now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
            
        elif 'yesterday' in time_text:
            # Format: "Yesterday, 10:30 AM"
            time_str = time_text.replace('yesterday,', '').strip()
            time_obj = datetime.strptime(time_str, '%I:%M %p')
            yesterday = now - timedelta(days=1)
            return yesterday.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
            
        else:
            # Format: "26 May 2025, 10:30 AM"
            try:
                dt = datetime.strptime(time_text, '%d %b %Y, %I:%M %p')
                return dt + IST_OFFSET
            except ValueError:
                # Try alternate format: "10:30 AM, 26 May 2025"
                try:
                    dt = datetime.strptime(time_text, '%I:%M %p, %d %b %Y')
                    return dt + IST_OFFSET
                except ValueError:
                    # If all parsing attempts fail, return current time
                    logger.warning(f"Could not parse time '{time_text}', using current time")
                    return get_ist_time()
                
    except Exception as e:
        logger.warning(f"Error parsing time '{time_text}', using current time: {str(e)}")
        return get_ist_time()

def is_within_last_12_hours(time_text: str) -> bool:
    """Check if the news time is within last 12 hours."""
    try:
        news_time = parse_news_time(time_text)
        if not news_time:
            return False
            
        current_time = get_ist_time()
        time_diff = current_time - news_time
        
        return time_diff <= timedelta(hours=12)
    except Exception as e:
        logger.error(f"Error checking time range: {str(e)}")
        return False

def scrape_pulse_zerodha():
    """
    Script to scrape Zerodha Pulse website using requests and BeautifulSoup
    """
    print("Starting Zerodha Pulse scraper...")
    
    # URL of the website
    url = "https://pulse.zerodha.com/"
    
    try:
        # Make the request with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        print("Fetching news from Zerodha Pulse...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the news list
        news_items = []
        news_list = soup.find('ul', id='news')
        
        if not news_list:
            print("Warning: News list not found in the page")
            return None
            
        items = news_list.find_all('li', class_='box item')
        print(f"Found {len(items)} total news items")
      
        print(f"Processing latest {len(items)} news items")
        
        for idx, item in enumerate(items, 1):
            try:
                # Extract headline with safe navigation
                headline_elem = item.select_one('h2.title a')
                if not headline_elem:
                    print(f"Skipping item {idx}: No headline found")
                    continue
                    
                headline = headline_elem.get_text(strip=True)
                if not headline:
                    print(f"Skipping item {idx}: Empty headline")
                    continue
                
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
                news_item = {
                    'headline': headline,
                    'description': description,
                    'source': source,
                    'time': time_text,
                    'url': url
                }
                
                news_items.append(news_item)
                print(f"Article {len(news_items)}: {headline[:50]}...")
                
            except Exception as e:
                print(f"Error processing article {idx}: {str(e)}")
                continue
        
        if not news_items:
            print("Warning: No valid news items were found")
            return None
            
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
            
        # Save to JSON file in data directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join('data', f"pulse_news_{timestamp}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(news_items, f, indent=4, ensure_ascii=False)
        
        print(f"\nSuccessfully scraped {len(news_items)} latest news items")
        print(f"Data saved to {filename}")
        
        return news_items
        
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None

class StreamlinedFinancialNewsAnalyzer:
    def __init__(self, groq_token: Optional[str] = None):
        """Initialize the Streamlined Financial News Analyzer"""
        if not groq_token:
            groq_token = get_groq_token()
            
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {groq_token}",
            "Content-Type": "application/json"
        } if groq_token else {}
        
        # Use efficient model for batch analysis
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
        self.max_context_tokens = 4000
        self.max_output_tokens = 1500
        self.batch_size = 15  # Larger batches for efficiency
        
        # Enhanced categorization
        self.sector_keywords = {
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

    def analyze_all_news_consolidated(self, news_data: List[Dict]) -> Dict:
        """Main analysis method that returns ONE FINAL REPORT."""
        logger.info(f"Starting consolidated analysis of {len(news_data)} news items...")
        
        # Step 1: Prioritize and categorize
        prioritized_news = self.prioritize_news(news_data)
        categorized_news = self.categorize_news_by_sector(prioritized_news)
        sector_summary = {k: len(v) for k, v in categorized_news.items()}
        
        logger.info(f"News categorized: {sector_summary}")
        
        # Step 2: Split into batches and extract key insights
        batches = self.split_into_batches(prioritized_news)
        logger.info(f"Processing {len(batches)} batches for key insights...")
        
        batch_insights = []
        total_api_calls = 0
        
        for i, batch in enumerate(batches, 1):
            insights = self.analyze_batch_for_insights(batch, i, len(batches))
            batch_insights.append(insights)
            total_api_calls += 1
            
            if i < len(batches):
                time.sleep(1)  # Rate limiting
        
        # Step 3: Generate final consolidated report
        logger.info("Generating final consolidated report...")
        final_report = self.generate_final_consolidated_report(batch_insights, sector_summary, len(news_data))
        total_api_calls += 1
        
        return {
            'total_news_items': len(news_data),
            'sector_summary': sector_summary,
            'final_report': final_report,
            'api_calls_used': total_api_calls,
            'analysis_timestamp': datetime.now().isoformat()
        }

    def prioritize_news(self, news_data: List[Dict]) -> List[Dict]:
        """Prioritize news based on market impact and recency."""
        def calculate_priority(news_item):
            score = 0
            headline = news_item.get('headline', '').lower()
            description = news_item.get('description', '').lower()
            combined_text = f"{headline} {description}"
            
            # High impact keywords
            high_impact_words = [
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
            
            for word in high_impact_words:
                if word in combined_text:
                    score += 3
            
            # Market moving events
            market_movers = [
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
            
            for word in market_movers:
                if word in combined_text:
                    score += 2
            
            # Financial figures
            if re.search(r'rs\s*\d+|₹\s*\d+|\d+\s*crore|\d+\s*%', combined_text):
                score += 2
            
            # Recent news gets higher priority
            time_str = news_item.get('time', '')
            if 'may 2025' in time_str.lower():
                score += 1
            
            return score
        
        return sorted(news_data, key=calculate_priority, reverse=True)

    def categorize_news_by_sector(self, news_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize news by sectors for better analysis."""
        categorized = {sector: [] for sector in self.sector_keywords.keys()}
        categorized['general'] = []
        
        for news_item in news_data:
            headline = news_item.get('headline', '').lower()
            description = news_item.get('description', '').lower()
            combined_text = f"{headline} {description}"
            
            assigned = False
            for sector, keywords in self.sector_keywords.items():
                if any(keyword in combined_text for keyword in keywords):
                    categorized[sector].append(news_item)
                    assigned = True
                    break
            
            if not assigned:
                categorized['general'].append(news_item)
        
        return categorized

    def split_into_batches(self, news_data: List[Dict]) -> List[List[Dict]]:
        """Split news data into batches."""
        return [news_data[i:i + self.batch_size] for i in range(0, len(news_data), self.batch_size)]

    def analyze_batch_for_insights(self, batch: List[Dict], batch_num: int, total_batches: int) -> str:
        """Analyze batch and extract structured insights."""
        logger.info(f"Extracting structured insights from batch {batch_num}/{total_batches} ({len(batch)} items)")
        
        # Prepare concise news summary
        news_summary = self.prepare_concise_batch_summary(batch)
        
        # Create focused prompt for structured insights with exact format
        prompt = f"""Extract structured insights from this news batch. Focus on specific companies, sectors, and actionable information.

NEWS BATCH {batch_num}/{total_batches}:
{news_summary}

Extract and organize in EXACTLY this format:

**Key Sector Trends** 🌍📈
- List sector-specific developments with company names and concrete details
- Include actual numbers and percentages where available
- Focus on market-moving news

**Buy/Sell Opportunities** 💰🔍
- Buy: List specific stocks with clear reasoning and target prices
- Sell/Avoid: List stocks to avoid with specific reasons
- Include analyst recommendations and technical levels

**Macro Implications** 🏦📉
- List government policies and regulatory changes
- Include economic indicators and market sentiment
- Focus on items affecting overall market direction

**Corporate Actions** 🗓️🏢
- List earnings results with specific numbers
- Include dividend announcements and business updates
- Mention upcoming corporate events

Keep each point concise but include specific company names, figures, and concrete details."""
        
        return self.query_groq_model(prompt)

    def prepare_concise_batch_summary(self, news_data: List[Dict]) -> str:
        """Prepare very concise summary for batch analysis."""
        news_summary = ""
        for i, news in enumerate(news_data, 1):
            headline = news.get('headline', '')[:80]
            description = news.get('description', '')[:100]
            news_summary += f"{i}. {headline} - {description}\n"
        return news_summary

    def generate_final_consolidated_report(self, batch_insights: List[str], sector_summary: Dict, total_items: int) -> str:
        """Generate structured report in the exact format requested."""
        
        # Combine all batch insights
        all_insights = "\n\n".join([f"BATCH {i+1} INSIGHTS:\n{insight}" for i, insight in enumerate(batch_insights)])
        
        sector_text = ", ".join([f"{sector.title()}({count})" for sector, count in sector_summary.items() if count > 0])
        
        consolidation_prompt = f"""You are a senior financial analyst. Create a structured report from these news insights in the EXACT format shown below.

SECTOR DISTRIBUTION: {sector_text}
TOTAL NEWS ANALYZED: {total_items}

ALL BATCH INSIGHTS:
{all_insights}

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

**Key Sector Trends** 🌍📈
- Sector name: Brief description of trend/development with specific company names and details mentioned in the news
- Another sector: Description with company names and specific developments
- Continue for all major sectors with news

**Buy/Sell Opportunities** 💰🔍
- Buy: List specific stock names with brief reasoning (technical breakouts, earnings, analyst recommendations)
- Sell/Avoid: List stocks to avoid with reasoning
- Include specific targets/levels where mentioned

**Macro Implications** 🏦📉
- List broader economic/policy impacts that affect markets
- Include government policies, international developments, regulatory changes
- Focus on items that impact overall market sentiment

**Corporate Actions** 🗓️🏢
- List specific companies with earnings results, dividend announcements, business updates
- Include actual numbers (revenue growth %, profit figures, etc.) where available
- Mention upcoming earnings/events

Use bullet points with clear company names and specific details. Keep each point concise but informative with actual data from the news."""
        
        return self.query_groq_model(consolidation_prompt)

    def query_groq_model(self, prompt: str, max_retries: int = 3) -> str:
        """Query Groq model with error handling."""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior financial analyst. Provide concise, actionable trading insights."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 800,  # Shorter responses
            "top_p": 0.8
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        return result['choices'][0]['message']['content'].strip()
                
                elif response.status_code == 429:
                    wait_time = 15 * (attempt + 1)
                    logger.warning(f"Rate limit hit, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                else:
                    logger.error(f"API Error: {response.status_code}")
                    return f"API Error: {response.status_code}"
                    
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(10)
                return f"Error: {str(e)}"
        
        return "Error: Max retries exceeded"

    def generate_clean_daily_report(self, results: Dict) -> str:
        """Generate a clean report in the requested structured format."""
        report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sector_text = " | ".join([f"{sector.title()}: {count}" 
                                 for sector, count in results['sector_summary'].items() if count > 0])
        
        # Create report with exact box formatting and emojis
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║                📈 STRUCTURED FINANCIAL NEWS REPORT 📈            ║
║                        {report_date}                      ║
╚══════════════════════════════════════════════════════════════════╝

📊 **Analysis Summary**: {results['total_news_items']} news items analyzed across sectors: {sector_text}

{results['final_report']}

📌 *Note: Analysis based on {results['total_news_items']} items processed through {results['api_calls_used']} AI analysis calls for comprehensive coverage.*
"""
        return report

    def save_report(self, report: str, filename: str = None) -> str:
        """Save the report to a file with consistent naming."""
        if not filename:
            # Use consistent timestamp format
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = os.path.join('data', f"zerodha_news_report_{timestamp}.txt")
        
        try:
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            
            # Save with UTF-8 encoding for emojis
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"📄 Report saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")
            return None

def main():
    """Main function to run the complete news scraping and analysis pipeline."""
    # Load environment variables
    load_dotenv()
    
    print("🚀 Starting Zerodha News Analysis Pipeline...")
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Get current timestamp for logging
    start_time = datetime.now()
    print(f"\n📅 Report Generation Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get Telegram credentials from environment variables
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not telegram_token or not telegram_chat_id:
        print("⚠️  Telegram credentials not found. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables to enable Telegram notifications.")
    
    # Step 1: Scrape news
    print("\n📰 Step 1: Scraping news from Zerodha Pulse...")
    news_data = scrape_pulse_zerodha()
    
    if not news_data:
        print("❌ Failed to scrape news. Exiting...")
        return
    
    # Step 2: Initialize analyzer with Telegram bot if credentials are available
    print("\n🔧 Step 2: Initializing Financial News Analyzer...")
    analyzer = StreamlinedFinancialNewsAnalyzer()
    
    # Step 3: Analyze news
    print("\n🔍 Step 3: Analyzing news for structured report...")
    results = analyzer.analyze_all_news_consolidated(news_data)
    
    # Step 4: Generate and save report
    print("\n📊 Step 4: Generating final report...")
    report = analyzer.generate_clean_daily_report(results)
    
    # Use current time for the report filename
    current_time = datetime.now()
    filename = os.path.join('data', f"zerodha_news_report_{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.txt")
    saved_file = analyzer.save_report(report, filename)
    
    # Display the report
    print("\n" + "="*80)
    print(report)
    print("="*80)
    
    if saved_file:
        print(f"\n💾 Report saved to: {saved_file}")
        
        # Send to Telegram if credentials are available
        if telegram_token and telegram_chat_id:
            try:
                print("\n📱 Sending report to Telegram...")
                telegram_bot = TelegramBot(telegram_token, telegram_chat_id)
                
                # Get the complete report text, removing decorative lines
                report_lines = []
                
                # Add a clear header
                report_lines.append("<b>📊 FINANCIAL NEWS REPORT</b>")
                report_lines.append(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                # Process each line with proper formatting
                for line in report.split('\n'):
                    line = line.strip()
                    # Skip decorative lines
                    if not line or line.startswith('╔') or line.startswith('║') or line.startswith('╚'):
                        continue
                        
                    # Format section headers
                    if line.startswith('**') and line.endswith('**'):
                        # Add extra newline before section headers
                        report_lines.append('')
                        line = f"<b>{line[2:-2].upper()}</b>"  # Remove ** and make uppercase
                    elif line.startswith('*'):
                        # Format subsection headers
                        line = f"<b>{line[1:]}</b>" if line.endswith('*') else f"<b>{line[1:]}</b>"
                    
                    # Format bullet points and numbering
                    if line.startswith('- '):
                        line = f"• {line[2:]}"
                    elif re.match(r'^\d+\.\s', line):
                        # Keep numbered lists as is
                        pass
                    
                    # No need to escape special characters for HTML
                    report_lines.append(line)
                
                # Add footer with analysis info
                report_lines.append('\n<b>Analysis Information</b>')
                report_lines.append(f"• Total News Items Analyzed: {results['total_news_items']}")
                report_lines.append(f"• AI Analysis Calls: {results['api_calls_used']}")
                report_lines.append(f"• Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Join lines and split into chunks if needed
                full_report = '\n'.join(report_lines)
                
                # Split the report into chunks if it exceeds the limit
                chunks = []
                max_length=4000;
                if len(full_report) > max_length:
                    # Split by double newlines to try to keep sections together
                    sections = full_report.split('\n\n')
                    current_chunk = []
                    current_length = 0
                    
                    for section in sections:
                        if current_length + len(section) + 2 > max_length:
                            if current_chunk:
                                chunks.append('\n\n'.join(current_chunk))
                            current_chunk = [section]
                            current_length = len(section)
                        else:
                            current_chunk.append(section)
                            current_length += len(section) + 2
                    
                    if current_chunk:
                        chunks.append('\n\n'.join(current_chunk))
                else:
                    chunks = [full_report]
                
                # Send each chunk as a separate message
                for i, chunk in enumerate(chunks, 1):
                    try:
                        # Add part number if there are multiple chunks
                        if len(chunks) > 1:
                            message = f"<b>📊 Financial News Report (Part {i}/{len(chunks)})</b>\n\n{chunk}"
                        else:
                            message = f"<b>📊 Financial News Report</b>\n\n{chunk}"
                            
                        # Use parse_mode='HTML' instead of 'Markdown'
                        if telegram_bot.send_message(message, parse_mode='HTML'):
                            print(f"✅ Successfully sent part {i}/{len(chunks)} to Telegram")
                        else:
                            print(f"❌ Failed to send part {i}/{len(chunks)} to Telegram")
                    except Exception as e:
                        print(f"❌ Error sending part {i}/{len(chunks)} to Telegram: {e}")
                
                print("📱 Telegram notification complete!")
                
            except Exception as e:
                print(f"❌ Error sending to Telegram: {e}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n✅ Analysis complete! Generated structured report with:")
    print(f"📅 Report Generation Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Total Processing Time: {duration.total_seconds():.2f} seconds")
    print("📈 Key Sector Trends | 💰 Buy/Sell Opportunities | 🏦 Macro Implications | 🏢 Corporate Actions")
    print(f"🔢 Used {results['api_calls_used']} API calls to analyze {results['total_news_items']} news items")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1) 