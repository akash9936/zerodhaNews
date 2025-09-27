"""
Main orchestrator for the Zerodha News Analysis Pipeline
"""
import os
import logging
from datetime import datetime
from typing import Optional, Dict

from dotenv import load_dotenv

from news_scraper import ZerodhaPulseScraper
from news_analyzer import NewsAnalyzer
from report_generator import ReportGenerator
from notification_service import NotificationService
from config import FileConfig, LoggingConfig

# Configure logging
logging.basicConfig(
    level=getattr(logging, LoggingConfig.LEVEL),
    format=LoggingConfig.FORMAT
)
logger = logging.getLogger(__name__)


class NewsAnalysisPipeline:
    """Main orchestrator for the news analysis pipeline"""

    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Initialize components
        self.scraper = ZerodhaPulseScraper()
        self.analyzer = NewsAnalyzer()
        self.report_generator = ReportGenerator()
        self.notification_service = NotificationService()

        # Ensure data directory exists
        os.makedirs(FileConfig.DATA_DIR, exist_ok=True)

    def run_complete_pipeline(self) -> Dict:
        """Run the complete news analysis pipeline."""
        start_time = datetime.now()
        logger.info("🚀 Starting Zerodha News Analysis Pipeline...")
        logger.info(f"📅 Report Generation Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Step 1: Scrape news
            logger.info("📰 Step 1: Scraping news from Zerodha Pulse...")
            news_data = self.scraper.scrape_news()

            if not news_data:
                logger.error("❌ Failed to scrape news. Exiting...")
                return {
                    'success': False,
                    'error': 'Failed to scrape news',
                    'start_time': start_time.isoformat(),
                    'end_time': datetime.now().isoformat()
                }

            # Save scraped data
            self.scraper.save_news_data(news_data)

            # Step 2: Analyze news
            logger.info("🔍 Step 2: Analyzing news for structured report...")
            results = self.analyzer.analyze_all_news_consolidated(news_data)

            # Step 3: Generate and save report
            logger.info("📊 Step 3: Generating final report...")
            report = self.report_generator.generate_clean_daily_report(results)

            # Save report to file
            current_time = datetime.now()
            filename = self.report_generator.get_report_filename(
                current_time.strftime(FileConfig.TIMESTAMP_FORMAT)
            )
            saved_file = self.report_generator.save_report(report, filename)

            # Step 4: Send notifications
            if saved_file:
                logger.info("📱 Step 4: Sending notifications...")
                notification_results = self.notification_service.send_notification(
                    results, self.report_generator
                )
            else:
                notification_results = {}

            # Calculate duration and log results
            end_time = datetime.now()
            duration = end_time - start_time

            pipeline_results = {
                'success': True,
                'news_items_scraped': len(news_data),
                'analysis_results': results,
                'report_file': saved_file,
                'notification_results': notification_results,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds()
            }

            self._log_completion_summary(pipeline_results)
            return pipeline_results

        except Exception as e:
            logger.error(f"❌ Pipeline failed with error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat()
            }

    def _log_completion_summary(self, results: Dict):
        """Log pipeline completion summary."""
        analysis_results = results['analysis_results']
        duration = results['duration_seconds']

        logger.info("✅ Analysis complete! Generated structured report with:")
        logger.info(f"📅 Report Generation Time: {results['start_time']}")
        logger.info(f"⏱️  Total Processing Time: {duration:.2f} seconds")
        logger.info("📈 Key Sector Trends | 💰 Buy/Sell Opportunities | 🏦 Macro Implications | 🏢 Corporate Actions")
        logger.info(f"🔢 Used {analysis_results['api_calls_used']} API calls to analyze {analysis_results['total_news_items']} news items")

        if results['report_file']:
            logger.info(f"💾 Report saved to: {results['report_file']}")

        # Log notification results
        notification_results = results['notification_results']
        for channel, success in notification_results.items():
            status = "✅" if success else "❌"
            logger.info(f"{status} {channel.title()} notification: {'Success' if success else 'Failed'}")

    def display_report(self, report: str):
        """Display the generated report."""
        print("\n" + "="*80)
        print(report)
        print("="*80)

    def run_pipeline_with_display(self) -> Dict:
        """Run pipeline and display the report."""
        results = self.run_complete_pipeline()

        if results['success']:
            # Generate and display the report
            analysis_results = results['analysis_results']
            report = self.report_generator.generate_clean_daily_report(analysis_results)
            self.display_report(report)

        return results


def main():
    """Main function to run the complete news scraping and analysis pipeline."""
    try:
        pipeline = NewsAnalysisPipeline()
        results = pipeline.run_pipeline_with_display()

        if not results['success']:
            logger.error("Pipeline execution failed")
            return 1

        return 0

    except KeyboardInterrupt:
        logger.info("Script interrupted by user. Exiting...")
        return 0
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())