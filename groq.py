import json
import requests
import time
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def count_tokens(text: str, model: str = None) -> int:
    """Roughly estimate token count (1 token ≈ 4 characters)."""
    return max(1, len(text) // 4)

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
    
    def prioritize_news(self, news_data: List[Dict]) -> List[Dict]:
        """Prioritize news based on market impact and recency."""
        def calculate_priority(news_item):
            score = 0
            headline = news_item.get('headline', '').lower()
            description = news_item.get('description', '').lower()
            combined_text = f"{headline} {description}"
            
            # High impact keywords
            high_impact_words = ['results', 'earnings', 'profit', 'loss', 'merger', 'acquisition', 
                               'ipo', 'dividend', 'buyback', 'split', 'delisting', 'rating', 
                               'upgrade', 'downgrade', 'target', 'recommendation']
            
            for word in high_impact_words:
                if word in combined_text:
                    score += 3
            
            # Market moving events
            market_movers = ['fii', 'dii', 'rbi', 'sebi', 'government', 'policy', 'tax', 
                           'interest rate', 'inflation', 'gdp', 'budget']
            
            for word in market_movers:
                if word in combined_text:
                    score += 2
            
            # Financial figures (indicates concrete data)
            if re.search(r'rs\s*\d+|₹\s*\d+|\d+\s*crore|\d+\s*%', combined_text):
                score += 2
            
            # Recent news gets higher priority
            time_str = news_item.get('time', '')
            if 'may 2025' in time_str.lower():
                score += 1
            
            return score
        
        # Sort by calculated priority
        sorted_news = sorted(news_data, key=calculate_priority, reverse=True)
        return sorted_news
    
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
    
    def analyze_batch_for_insights(self, batch: List[Dict], batch_num: int, total_batches: int) -> str:
        """Analyze batch and extract structured insights."""
        logger.info(f"Extracting structured insights from batch {batch_num}/{total_batches} ({len(batch)} items)")
        
        # Prepare concise news summary
        news_summary = self.prepare_concise_batch_summary(batch)
        
        # Create focused prompt for structured insights
        prompt = f"""Extract structured insights from this news batch. Focus on specific companies, sectors, and actionable information.

NEWS BATCH {batch_num}/{total_batches}:
{news_summary}

Extract and organize:
1. SECTOR DEVELOPMENTS: Which sectors have significant news with specific company names and developments
2. STOCK RECOMMENDATIONS: Any buy/sell recommendations, analyst calls, or breakout stocks mentioned
3. EARNINGS/CORPORATE ACTIONS: Companies reporting results, dividends, business updates with specific numbers
4. MACRO/POLICY NEWS: Government policies, regulatory changes, economic developments affecting markets

Include specific company names, actual figures (revenue, profit, growth %), and concrete details from the news.
Keep response under 300 words but include all key details."""
        
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
        
        consolidation_prompt = f"""You are a financial analyst. Create a structured report from these news insights in the EXACT format shown below.

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
    
    def analyze_all_news_consolidated(self, news_data: List[Dict]) -> Dict:
        """Main analysis method that returns ONE FINAL REPORT."""
        logger.info(f"Starting consolidated analysis of {len(news_data)} news items...")
        
        # Step 1: Prioritize and categorize
        prioritized_news = self.prioritize_news(news_data)
        categorized_news = self.categorize_news_by_sector(prioritized_news)
        sector_summary = {k: len(v) for k, v in categorized_news.items()}
        
        logger.info(f"News categorized: {sector_summary}")
        
        # Step 2: Split into batches and extract key insights only
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
        
        # Step 3: Generate ONE FINAL consolidated report
        logger.info("Generating final consolidated report...")
        final_report = self.generate_final_consolidated_report(batch_insights, sector_summary, len(news_data))
        total_api_calls += 1
        
        # Calculate token usage
        total_input_tokens = sum(count_tokens(insight) for insight in batch_insights) + count_tokens(final_report)
        total_output_tokens = count_tokens(final_report)
        
        return {
            'total_news_items': len(news_data),
            'sector_summary': sector_summary,
            'final_report': final_report,
            'api_calls_used': total_api_calls,
            'input_tokens': total_input_tokens,
            'output_tokens': total_output_tokens,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def split_into_batches(self, news_data: List[Dict]) -> List[List[Dict]]:
        """Split news data into batches."""
        return [news_data[i:i + self.batch_size] for i in range(0, len(news_data), self.batch_size)]
    
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
        
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║                📈 STRUCTURED FINANCIAL NEWS REPORT 📈            ║
║                        {report_date}                      ║
╚══════════════════════════════════════════════════════════════════╝

📊 **Analysis Summary**: {results['total_news_items']} news items analyzed across sectors: {sector_text}

{results['final_report']}

*Note: The news analysis is based on {results['total_news_items']} items processed through {results['api_calls_used']} AI analysis calls for comprehensive coverage.*
"""
        return report
    
    def save_report(self, report: str, filename: str = None) -> str:
        """Save the report to a file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"trading_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return None


def main():
    """Main function generating structured financial news report."""
    print("🚀 Starting Structured Financial News Analysis...")
    
    # Load news data
    try:
        news_files = [f for f in os.listdir('.') if f.startswith('pulse_news_') and f.endswith('.json')]
        if not news_files:
            print("❌ No news files found. Looking for files starting with 'pulse_news_' and ending with '.json'")
            return
        
        latest_file = sorted(news_files)[-1]
        print(f"📰 Loading news from: {latest_file}")
        
        with open(latest_file, 'r') as f:
            news_data = json.load(f)
        
        print(f"✅ Loaded {len(news_data)} news items")
        
    except Exception as e:
        print(f"❌ Error loading news file: {e}")
        return
    
    # Initialize analyzer
    print("🔧 Initializing Financial News Analyzer...")
    analyzer = StreamlinedFinancialNewsAnalyzer()
    
    # Perform consolidated analysis
    print("🔍 Analyzing news for structured report...")
    results = analyzer.analyze_all_news_consolidated(news_data)
    
    # Generate structured report
    report = analyzer.generate_clean_daily_report(results)
    
    # Save report
    saved_file = analyzer.save_report(report)
    
    # Display the structured report
    print("\n" + "="*80)
    print(report)
    print("="*80)
    
    if saved_file:
        print(f"\n💾 Structured report saved to: {saved_file}")
    
    print(f"\n✅ Analysis complete! Generated structured report with:")
    print("📈 Key Sector Trends | 💰 Buy/Sell Opportunities | 🏦 Macro Implications | 🏢 Corporate Actions")
    print(f"🔢 Used {results['api_calls_used']} API calls to analyze {results['total_news_items']} news items")

if __name__ == "__main__":
    main()