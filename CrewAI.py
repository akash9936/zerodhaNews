import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IST is UTC+5:30
IST_OFFSET = timedelta(hours=5, minutes=30)

def get_ist_time() -> datetime:
    """Get current time in IST."""
    return datetime.utcnow() + IST_OFFSET

# Custom Tools for CrewAI
class NewsScrapingTool(BaseTool):
    name: str = "news_scraper"
    description: str = "Scrapes financial news from Zerodha Pulse website"
    
    def _run(self) -> List[Dict]:
        """Scrape news from Zerodha Pulse"""
        url = "https://pulse.zerodha.com/"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            logger.info("Fetching news from Zerodha Pulse...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []
            news_list = soup.find('ul', id='news')
            
            if not news_list:
                logger.warning("News list not found in the page")
                return []
                
            items = news_list.find_all('li', class_='box item')
            logger.info(f"Found {len(items)} total news items")
          
            for idx, item in enumerate(items, 1):
                try:
                    headline_elem = item.select_one('h2.title a')
                    if not headline_elem:
                        continue
                        
                    headline = headline_elem.get_text(strip=True)
                    if not headline:
                        continue
                    
                    desc_elem = item.select_one('div.desc')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    date_elem = item.select_one('div.date')
                    time_text = ""
                    if date_elem:
                        time_text = date_elem.get('title', '') or date_elem.get_text(strip=True)
                    if not time_text:
                        time_text = "Unknown time"
                    
                    source_elem = item.select_one('div.feed')
                    source = "Unknown source"
                    if source_elem:
                        source = source_elem.get_text(strip=True).replace("—", "").strip()
                    
                    url = headline_elem.get('href', '')
                    
                    news_item = {
                        'headline': headline,
                        'description': description,
                        'source': source,
                        'time': time_text,
                        'url': url
                    }
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.error(f"Error processing article {idx}: {str(e)}")
                    continue
            
            # Save scraped data
            os.makedirs('data', exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join('data', f"pulse_news_{timestamp}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(news_items, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Successfully scraped {len(news_items)} news items")
            return news_items
            
        except Exception as e:
            logger.error(f"Error scraping news: {str(e)}")
            return []

class GroqAnalysisTool(BaseTool):
    name: str = "groq_analyzer"
    description: str = "Analyzes financial news using Groq LLM API"
    groq_token: str = Field(default=None, exclude=True)
    base_url: str = Field(default="https://api.groq.com/openai/v1/chat/completions")
    headers: Dict = Field(default_factory=dict)
    model: str = Field(default="llama-3.1-70b-versatile")
    
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.groq_token = os.getenv("GROQ_API_KEY")
        if not self.groq_token:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.headers = {
            "Authorization": f"Bearer {self.groq_token}",
            "Content-Type": "application/json"
        }
    
    def _run(self, news_batch: List[Dict], analysis_type: str = "general") -> str:
        """Analyze news batch using Groq API"""
        
        # Prepare news summary
        news_summary = ""
        for i, news in enumerate(news_batch, 1):
            headline = news.get('headline', '')[:80]
            description = news.get('description', '')[:100]
            news_summary += f"{i}. {headline} - {description}\n"
        
        # Create analysis prompt based on type
        if analysis_type == "sector_analysis":
            prompt = f"""Analyze the following financial news and categorize by sectors. Identify key trends in each sector:

NEWS DATA:
{news_summary}

Provide analysis in this format:
**Sector Analysis**
- Banking: [trends and key developments]
- Technology: [trends and key developments]
- Pharma: [trends and key developments]
- Auto: [trends and key developments]
- Other sectors: [as applicable]
"""
        elif analysis_type == "trading_opportunities":
            prompt = f"""Analyze the following financial news for trading opportunities:

NEWS DATA:
{news_summary}

Provide analysis in this format:
**Trading Opportunities**
- Buy Recommendations: [stocks with reasoning]
- Sell/Avoid: [stocks with reasoning]
- Watch List: [stocks to monitor]
"""
        else:  # general analysis
            prompt = f"""Provide a comprehensive analysis of the following financial news:

NEWS DATA:
{news_summary}

Focus on:
1. Market sentiment and trends
2. Key corporate developments
3. Sector-wise implications
4. Investment opportunities and risks
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior financial analyst providing actionable market insights."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
            "top_p": 0.8
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Groq API Error: {response.status_code}")
                return f"Analysis failed: API Error {response.status_code}"
                
        except Exception as e:
            logger.error(f"Groq API request failed: {str(e)}")
            return f"Analysis failed: {str(e)}"

class ReportGeneratorTool(BaseTool):
    name: str = "report_generator"
    description: str = "Generates structured financial reports"
    
    def _run(self, analysis_results: Dict, news_count: int) -> str:
        """Generate final structured report"""
        
        report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║                📈 CREWAI FINANCIAL NEWS REPORT 📈               ║
║                        {report_date}                      ║
╚══════════════════════════════════════════════════════════════════╝

📊 **Analysis Summary**: {news_count} news items analyzed

{analysis_results.get('sector_analysis', '')}

{analysis_results.get('trading_opportunities', '')}

{analysis_results.get('market_overview', '')}

📌 *Report generated using CrewAI multi-agent system*
"""
        return report

# CrewAI Agents
def create_news_scraper_agent():
    """Create news scraping agent"""
    return Agent(
        role='Financial News Scraper',
        goal='Scrape and collect the latest financial news from reliable sources',
        backstory='You are an expert web scraper specialized in gathering financial news data from various sources, particularly Zerodha Pulse.',
        tools=[NewsScrapingTool()],
        verbose=True,
        allow_delegation=False
    )

def create_sector_analyst_agent():
    """Create sector analysis agent"""
    return Agent(
        role='Sector Analysis Specialist',
        goal='Analyze financial news by sectors and identify key trends',
        backstory='You are a seasoned sector analyst with deep knowledge of various market sectors including banking, technology, pharma, auto, and others.',
        tools=[GroqAnalysisTool()],
        verbose=True,
        allow_delegation=False
    )

def create_trading_strategist_agent():
    """Create trading strategy agent"""
    return Agent(
        role='Trading Strategy Analyst',
        goal='Identify trading opportunities and provide investment recommendations',
        backstory='You are an experienced trading strategist who specializes in identifying buy/sell opportunities and market timing.',
        tools=[GroqAnalysisTool()],
        verbose=True,
        allow_delegation=False
    )

def create_report_writer_agent():
    """Create report writing agent"""
    return Agent(
        role='Financial Report Writer',
        goal='Compile comprehensive financial reports from analysis results',
        backstory='You are a professional financial report writer who creates clear, structured reports for investment decision-making.',
        tools=[ReportGeneratorTool()],
        verbose=True,
        allow_delegation=False
    )

# CrewAI Tasks
def create_scraping_task(agent):
    """Create news scraping task"""
    return Task(
        description="Scrape the latest financial news from Zerodha Pulse website and return the structured news data.",
        agent=agent,
        expected_output="A list of dictionaries containing news headlines, descriptions, sources, timestamps, and URLs."
    )

def create_sector_analysis_task(agent, news_data):
    """Create sector analysis task"""
    return Task(
        description=f"Analyze the scraped news data for sector-wise trends and developments. News data: {json.dumps(news_data[:10])}...",  # Pass sample data
        agent=agent,
        expected_output="Detailed sector-wise analysis highlighting key trends, major developments, and sector performance indicators."
    )

def create_trading_analysis_task(agent, news_data):
    """Create trading analysis task"""
    return Task(
        description=f"Analyze the news data to identify trading opportunities, buy/sell recommendations. News data: {json.dumps(news_data[:10])}...",
        agent=agent,
        expected_output="Trading recommendations with buy, sell, and watch list suggestions along with reasoning."
    )

def create_report_generation_task(agent, analysis_results, news_count):
    """Create report generation task"""
    return Task(
        description=f"Generate a comprehensive structured financial report from analysis results. Results: {analysis_results}, News count: {news_count}",
        agent=agent,
        expected_output="A well-formatted financial report with sections for sector analysis, trading opportunities, and market overview."
    )

# Main CrewAI Financial Analysis System
class CrewAIFinancialAnalyzer:
    def __init__(self):
        """Initialize the CrewAI system"""
        self.news_scraper = create_news_scraper_agent()
        self.sector_analyst = create_sector_analyst_agent()
        self.trading_strategist = create_trading_strategist_agent()
        self.report_writer = create_report_writer_agent()
        
    def run_analysis(self):
        """Run the complete financial analysis workflow"""
        logger.info("🚀 Starting CrewAI Financial Analysis Pipeline...")
        
        # Step 1: Scrape News
        scraping_task = create_scraping_task(self.news_scraper)
        
        crew_scraper = Crew(
            agents=[self.news_scraper],
            tasks=[scraping_task],
            process=Process.sequential,
            verbose=True
        )
        
        logger.info("📰 Scraping financial news...")
        scraping_result = crew_scraper.kickoff()
        
        # Parse the scraped data (assuming it returns the news list)
        news_data = NewsScrapingTool()._run()  # Direct call for simplicity
        
        if not news_data or len(news_data) == 0:
            logger.error("❌ No news data scraped. Exiting...")
            return None
        
        logger.info(f"✅ Successfully scraped {len(news_data)} news items")
        
        # Step 2: Parallel Analysis
        sector_task = create_sector_analysis_task(self.sector_analyst, news_data)
        trading_task = create_trading_analysis_task(self.trading_strategist, news_data)
        
        analysis_crew = Crew(
            agents=[self.sector_analyst, self.trading_strategist],
            tasks=[sector_task, trading_task],
            process=Process.hierarchical,  # Can run in parallel
            verbose=True
        )
        
        logger.info("🔍 Running sector and trading analysis...")
        analysis_results = analysis_crew.kickoff()
        
        # Step 3: Generate Report
        report_data = {
            'sector_analysis': "Sector analysis completed",  # This would contain actual results
            'trading_opportunities': "Trading analysis completed",
            'market_overview': f"Analysis of {len(news_data)} news items completed"
        }
        
        report_task = create_report_generation_task(self.report_writer, report_data, len(news_data))
        
        report_crew = Crew(
            agents=[self.report_writer],
            tasks=[report_task],
            process=Process.sequential,
            verbose=True
        )
        
        logger.info("📊 Generating final report...")
        final_report = report_crew.kickoff()
        
        # Save report
        self.save_report(str(final_report))
        
        return final_report
    
    def save_report(self, report: str, filename: str = None):
        """Save the generated report"""
        if not filename:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = os.path.join('data', f"crewai_financial_report_{timestamp}.txt")
        
        try:
            os.makedirs('data', exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"📄 Report saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")
            return None

def main():
    """Main function to run CrewAI financial analysis"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Check for required environment variables
        if not os.getenv("GROQ_API_KEY"):
            logger.error("❌ GROQ_API_KEY not found in environment variables")
            logger.info("Please set your Groq API key in the .env file")
            return
        
        # Initialize and run CrewAI system
        analyzer = CrewAIFinancialAnalyzer()
        result = analyzer.run_analysis()
        
        if result:
            print("\n" + "="*80)
            print(result)
            print("="*80)
            logger.info("✅ CrewAI Financial Analysis completed successfully!")
        else:
            logger.error("❌ Analysis failed")
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Analysis interrupted by user")
    except Exception as e:
        logger.error(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()