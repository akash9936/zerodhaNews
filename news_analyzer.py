"""
Core news analysis functionality using Groq API
"""
import time
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime

from config import GroqConfig, AnalysisConfig
from utils.api_utils import get_groq_token
from utils.text_utils import (
    calculate_news_priority_score,
    categorize_news_by_keywords,
    prepare_concise_batch_summary
)

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """Core news analysis engine using Groq API"""

    def __init__(self, groq_token: Optional[str] = None):
        """Initialize the News Analyzer"""
        if not groq_token:
            groq_token = get_groq_token()

        self.base_url = GroqConfig.BASE_URL
        self.headers = {
            "Authorization": f"Bearer {groq_token}",
            "Content-Type": "application/json"
        } if groq_token else {}

        self.model = GroqConfig.MODEL
        self.max_context_tokens = GroqConfig.MAX_CONTEXT_TOKENS
        self.max_output_tokens = GroqConfig.MAX_OUTPUT_TOKENS
        self.batch_size = AnalysisConfig.BATCH_SIZE

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
                time.sleep(AnalysisConfig.RATE_LIMIT_DELAY)

        # Step 3: Generate final consolidated report
        logger.info("Generating final consolidated report...")
        final_report = self.generate_final_consolidated_report(
            batch_insights, sector_summary, len(news_data)
        )
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
            return calculate_news_priority_score(
                news_item,
                AnalysisConfig.HIGH_IMPACT_KEYWORDS,
                AnalysisConfig.MARKET_MOVER_KEYWORDS
            )

        return sorted(news_data, key=calculate_priority, reverse=True)

    def categorize_news_by_sector(self, news_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize news by sectors for better analysis."""
        categorized = {sector: [] for sector in AnalysisConfig.SECTOR_KEYWORDS.keys()}
        categorized['general'] = []

        for news_item in news_data:
            sector = categorize_news_by_keywords(news_item, AnalysisConfig.SECTOR_KEYWORDS)
            categorized[sector].append(news_item)

        return categorized

    def split_into_batches(self, news_data: List[Dict]) -> List[List[Dict]]:
        """Split news data into batches."""
        return [news_data[i:i + self.batch_size] for i in range(0, len(news_data), self.batch_size)]

    def analyze_batch_for_insights(self, batch: List[Dict], batch_num: int, total_batches: int) -> str:
        """Analyze batch and extract structured insights."""
        logger.info(f"Extracting structured insights from batch {batch_num}/{total_batches} ({len(batch)} items)")

        # Prepare concise news summary
        news_summary = prepare_concise_batch_summary(batch)

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

    def generate_final_consolidated_report(self, batch_insights: List[str],
                                         sector_summary: Dict, total_items: int) -> str:
        """Generate structured report in the exact format requested."""

        # Combine all batch insights
        all_insights = "\n\n".join([f"BATCH {i+1} INSIGHTS:\n{insight}"
                                   for i, insight in enumerate(batch_insights)])

        sector_text = ", ".join([f"{sector.title()}({count})"
                               for sector, count in sector_summary.items() if count > 0])

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

    def query_groq_model(self, prompt: str, max_retries: int = None) -> str:
        """Query Groq model with error handling."""
        if max_retries is None:
            max_retries = GroqConfig.MAX_RETRIES

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
            "temperature": GroqConfig.TEMPERATURE,
            "max_tokens": GroqConfig.MAX_TOKENS,
            "top_p": GroqConfig.TOP_P
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=GroqConfig.TIMEOUT
                )

                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        return result['choices'][0]['message']['content'].strip()

                elif response.status_code == 429:
                    wait_time = AnalysisConfig.RATE_LIMIT_RETRY_DELAY * (attempt + 1)
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
                    continue
                return f"Error: {str(e)}"

        return "Error: Max retries exceeded"