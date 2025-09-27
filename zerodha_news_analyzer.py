"""
Refactored Zerodha News Analyzer - Now uses modular architecture

This file serves as a compatibility layer and entry point.
For new implementations, use pipeline_orchestrator.py directly.
"""
import sys
from pipeline_orchestrator import NewsAnalysisPipeline

# Legacy function for backward compatibility
def scrape_pulse_zerodha():
    """Legacy function - use ZerodhaPulseScraper class instead"""
    from news_scraper import ZerodhaPulseScraper
    scraper = ZerodhaPulseScraper()
    news_data = scraper.scrape_news()
    if news_data:
        scraper.save_news_data(news_data)
    return news_data

# Legacy class for backward compatibility
class StreamlinedFinancialNewsAnalyzer:
    """Legacy class - use NewsAnalyzer class instead"""
    def __init__(self, groq_token=None):
        from news_analyzer import NewsAnalyzer
        self._analyzer = NewsAnalyzer(groq_token)

    def analyze_all_news_consolidated(self, news_data):
        return self._analyzer.analyze_all_news_consolidated(news_data)

    def generate_clean_daily_report(self, results):
        from report_generator import ReportGenerator
        generator = ReportGenerator()
        return generator.generate_clean_daily_report(results)

    def save_report(self, report, filename=None):
        from report_generator import ReportGenerator
        generator = ReportGenerator()
        return generator.save_report(report, filename)

def main():
    """Main function - uses new modular pipeline."""
    pipeline = NewsAnalysisPipeline()
    results = pipeline.run_pipeline_with_display()
    return 0 if results['success'] else 1

if __name__ == "__main__":
    sys.exit(main()) 