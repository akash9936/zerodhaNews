"""
Time-related utility functions
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from config import IST_OFFSET

logger = logging.getLogger(__name__)


def get_ist_time() -> datetime:
    """Get current time in IST."""
    return datetime.utcnow() + IST_OFFSET


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


def format_timestamp(format_str: str = '%Y-%m-%d_%H-%M-%S') -> str:
    """Generate formatted timestamp string."""
    return datetime.now().strftime(format_str)


def format_json_timestamp() -> str:
    """Generate timestamp for JSON filenames."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')