"""
API-related utility functions
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

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


def get_telegram_credentials() -> tuple[Optional[str], Optional[str]]:
    """Get Telegram bot credentials from environment variables."""
    load_dotenv()
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    return telegram_token, telegram_chat_id


def check_safari_setup():
    """Check if Safari is properly set up for automation"""
    print("Checking Safari setup...")
    print("\nPlease ensure you have:")
    print("1. Enabled the Develop menu in Safari (Safari > Settings > Advanced > Show Develop menu)")
    print("2. Enabled Remote Automation (Develop > Allow Remote Automation)")
    print("3. Trusted the WebDriver in System Preferences > Security & Privacy")
    print("\nPress Enter to continue or Ctrl+C to exit...")
    input()