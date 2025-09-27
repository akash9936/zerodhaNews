"""
Text processing utility functions
"""
import re
from typing import List, Dict


def calculate_news_priority_score(news_item: Dict, high_impact_keywords: List[str],
                                market_mover_keywords: List[str]) -> int:
    """Calculate priority score for a news item based on keywords."""
    score = 0
    headline = news_item.get('headline', '').lower()
    description = news_item.get('description', '').lower()
    combined_text = f"{headline} {description}"

    # High impact keywords
    for word in high_impact_keywords:
        if word in combined_text:
            score += 3

    # Market moving events
    for word in market_mover_keywords:
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


def categorize_news_by_keywords(news_item: Dict, sector_keywords: Dict[str, List[str]]) -> str:
    """Categorize a news item by sector based on keywords."""
    headline = news_item.get('headline', '').lower()
    description = news_item.get('description', '').lower()
    combined_text = f"{headline} {description}"

    for sector, keywords in sector_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            return sector

    return 'general'


def clean_text_for_telegram(text: str) -> str:
    """Clean text for Telegram HTML formatting."""
    # Remove decorative lines
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line or line.startswith('╔') or line.startswith('║') or line.startswith('╚'):
            continue
        lines.append(line)
    return '\n'.join(lines)


def format_telegram_section_header(line: str) -> str:
    """Format section headers for Telegram."""
    if line.startswith('**') and line.endswith('**'):
        return f"<b>{line[2:-2].upper()}</b>"
    elif line.startswith('*') and line.endswith('*') and len(line) > 2:
        return f"<b>{line[1:-1]}</b>"
    elif line.startswith('*'):
        return f"<b>{line[1:]}</b>"
    return line


def format_telegram_bullet_points(line: str) -> str:
    """Format bullet points for Telegram."""
    if line.startswith('- '):
        return f"• {line[2:]}"
    elif re.match(r'^\d+\.\s', line):
        # Keep numbered lists as is
        return line
    return line


def split_text_into_chunks(text: str, max_length: int = 4000) -> List[str]:
    """Split text into chunks for Telegram message limits."""
    chunks = []
    if len(text) <= max_length:
        return [text]

    # Split by double newlines to try to keep sections together
    sections = text.split('\n\n')
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

    return chunks


def prepare_concise_batch_summary(news_data: List[Dict]) -> str:
    """Prepare very concise summary for batch analysis."""
    news_summary = ""
    for i, news in enumerate(news_data, 1):
        headline = news.get('headline', '')[:80]
        description = news.get('description', '')[:100]
        news_summary += f"{i}. {headline} - {description}\n"
    return news_summary