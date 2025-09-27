"""
Notification service for sending reports via Telegram
"""
import logging
from typing import Dict, Optional
from telegram_bot import TelegramBot
from config import TelegramConfig
from utils.api_utils import get_telegram_credentials
from utils.text_utils import split_text_into_chunks
from report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via various channels"""

    def __init__(self):
        self.telegram_token, self.telegram_chat_id = get_telegram_credentials()
        self.telegram_bot = None

        if self.telegram_token and self.telegram_chat_id:
            self.telegram_bot = TelegramBot(self.telegram_token, self.telegram_chat_id)
        else:
            logger.warning("Telegram credentials not found. Telegram notifications disabled.")

    def is_telegram_enabled(self) -> bool:
        """Check if Telegram notifications are enabled."""
        return self.telegram_bot is not None

    def send_telegram_report(self, results: Dict, report_generator: ReportGenerator) -> bool:
        """Send report to Telegram in properly formatted chunks."""
        if not self.is_telegram_enabled():
            logger.warning("Telegram notifications are not enabled")
            return False

        try:
            logger.info("Sending report to Telegram...")

            # Generate Telegram-optimized content
            full_report = report_generator.generate_telegram_report_content(results)

            # Split the report into chunks if needed
            chunks = split_text_into_chunks(full_report, TelegramConfig.MAX_MESSAGE_LENGTH)

            # Send each chunk as a separate message
            success_count = 0
            for i, chunk in enumerate(chunks, 1):
                try:
                    # Add part number if there are multiple chunks
                    if len(chunks) > 1:
                        message = f"<b>📊 Financial News Report (Part {i}/{len(chunks)})</b>\n\n{chunk}"
                    else:
                        message = f"<b>📊 Financial News Report</b>\n\n{chunk}"

                    # Send message with HTML formatting
                    if self.telegram_bot.send_message(message, parse_mode=TelegramConfig.PARSE_MODE):
                        logger.info(f"✅ Successfully sent part {i}/{len(chunks)} to Telegram")
                        success_count += 1
                    else:
                        logger.error(f"❌ Failed to send part {i}/{len(chunks)} to Telegram")

                except Exception as e:
                    logger.error(f"❌ Error sending part {i}/{len(chunks)} to Telegram: {e}")

            if success_count == len(chunks):
                logger.info("📱 Telegram notification complete!")
                return True
            else:
                logger.warning(f"📱 Partial Telegram success: {success_count}/{len(chunks)} chunks sent")
                return False

        except Exception as e:
            logger.error(f"❌ Error sending to Telegram: {e}")
            return False

    def send_notification(self, results: Dict, report_generator: ReportGenerator) -> Dict[str, bool]:
        """Send notifications via all enabled channels."""
        notification_results = {}

        # Send via Telegram
        if self.is_telegram_enabled():
            notification_results['telegram'] = self.send_telegram_report(results, report_generator)
        else:
            notification_results['telegram'] = False
            logger.info("⚠️  Telegram credentials not found. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables to enable Telegram notifications.")

        return notification_results