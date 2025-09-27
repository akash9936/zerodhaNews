"""
Report generation and formatting functionality
"""
import os
import logging
from typing import Dict, Optional
from datetime import datetime

from config import FileConfig
from utils.time_utils import format_timestamp

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Handles report generation, formatting, and saving"""

    def __init__(self):
        self.data_dir = FileConfig.DATA_DIR
        self.encoding = FileConfig.ENCODING

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

    def save_report(self, report: str, filename: str = None) -> Optional[str]:
        """Save the report to a file with consistent naming."""
        if not filename:
            # Use consistent timestamp format
            timestamp = format_timestamp(FileConfig.TIMESTAMP_FORMAT)
            filename = os.path.join(
                self.data_dir,
                FileConfig.REPORT_FILENAME_FORMAT.format(timestamp=timestamp)
            )

        try:
            # Ensure data directory exists
            os.makedirs(self.data_dir, exist_ok=True)

            # Save with UTF-8 encoding for emojis
            with open(filename, 'w', encoding=self.encoding) as f:
                f.write(report)
            logger.info(f"📄 Report saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")
            return None

    def generate_telegram_report_content(self, results: Dict) -> str:
        """Generate report content optimized for Telegram formatting."""
        from utils.time_utils import get_ist_time

        # Add a clear header
        report_lines = []
        report_lines.append("<b>📊 FINANCIAL NEWS REPORT</b>")
        report_lines.append(f"<b>Generated:</b> {get_ist_time().strftime('%Y-%m-%d %H:%M:%S')} IST\n")

        # Process the main report content
        report_content = results['final_report']
        for line in report_content.split('\n'):
            line = line.strip()
            if not line:
                report_lines.append('')
                continue

            # Format section headers
            if line.startswith('**') and line.endswith('**'):
                # Add extra newline before section headers
                report_lines.append('')
                line = f"<b>{line[2:-2].upper()}</b>"  # Remove ** and make uppercase
            elif line.startswith('*') and line.endswith('*') and len(line) > 2:
                # Format subsection headers with both asterisks
                line = f"<b>{line[1:-1]}</b>"
            elif line.startswith('*'):
                # Format subsection headers with single asterisk
                line = f"<b>{line[1:]}</b>"

            # Format bullet points and numbering
            if line.startswith('- '):
                line = f"• {line[2:]}"

            report_lines.append(line)

        # Add footer with analysis info
        report_lines.append('\n<b>Analysis Information</b>')
        report_lines.append(f"• Total News Items Analyzed: {results['total_news_items']}")
        report_lines.append(f"• AI Analysis Calls: {results['api_calls_used']}")
        report_lines.append(f"• Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return '\n'.join(report_lines)

    def format_report_summary(self, results: Dict) -> str:
        """Format a summary of the report generation process."""
        duration = "N/A"  # Could be passed from main orchestrator
        summary = f"""
✅ Analysis complete! Generated structured report with:
📈 Key Sector Trends | 💰 Buy/Sell Opportunities | 🏦 Macro Implications | 🏢 Corporate Actions
🔢 Used {results['api_calls_used']} API calls to analyze {results['total_news_items']} news items
        """
        return summary.strip()

    def get_report_filename(self, timestamp: Optional[str] = None) -> str:
        """Generate report filename with timestamp."""
        if not timestamp:
            timestamp = format_timestamp(FileConfig.TIMESTAMP_FORMAT)
        return os.path.join(
            self.data_dir,
            FileConfig.REPORT_FILENAME_FORMAT.format(timestamp=timestamp)
        )