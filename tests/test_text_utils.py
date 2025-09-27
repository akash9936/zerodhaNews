"""
Unit tests for text_utils module
"""
import pytest
from utils.text_utils import (
    calculate_news_priority_score,
    categorize_news_by_keywords,
    clean_text_for_telegram,
    format_telegram_section_header,
    format_telegram_bullet_points,
    split_text_into_chunks,
    prepare_concise_batch_summary
)


class TestTextUtils:

    def test_calculate_news_priority_score_high_impact(self):
        """Test priority score calculation for high impact keywords"""
        news_item = {
            'headline': 'HDFC Bank reports strong earnings with 20% profit growth',
            'description': 'The bank announced dividend and merger news',
            'time': 'May 2025'
        }
        high_impact = ['earnings', 'profit', 'dividend', 'merger']
        market_movers = ['bank']

        score = calculate_news_priority_score(news_item, high_impact, market_movers)
        # Should get points for: earnings(3) + profit(3) + dividend(3) + merger(3) + bank(2) + may 2025(1) = 15
        assert score >= 10  # At least 10 points from various factors

    def test_calculate_news_priority_score_financial_figures(self):
        """Test priority score for financial figures"""
        news_item = {
            'headline': 'Company reports Rs 1000 crore revenue',
            'description': 'Growth of 25% in quarterly results',
            'time': 'Today'
        }
        high_impact = []
        market_movers = []

        score = calculate_news_priority_score(news_item, high_impact, market_movers)
        # Should get 2 points for financial figure (Rs 1000 crore) and 2 points for percentage
        assert score >= 2

    def test_calculate_news_priority_score_no_keywords(self):
        """Test priority score with no matching keywords"""
        news_item = {
            'headline': 'Random news without keywords',
            'description': 'Generic description',
            'time': 'Unknown'
        }
        high_impact = ['earnings']
        market_movers = ['bank']

        score = calculate_news_priority_score(news_item, high_impact, market_movers)
        assert score == 0

    def test_categorize_news_by_keywords_banking(self):
        """Test news categorization for banking sector"""
        news_item = {
            'headline': 'HDFC Bank announces new credit policy',
            'description': 'The bank focuses on retail lending'
        }
        sector_keywords = {
            'banking': ['bank', 'credit'],
            'technology': ['tech', 'software']
        }

        category = categorize_news_by_keywords(news_item, sector_keywords)
        assert category == 'banking'

    def test_categorize_news_by_keywords_general(self):
        """Test news categorization for general category"""
        news_item = {
            'headline': 'Random market news',
            'description': 'General market update'
        }
        sector_keywords = {
            'banking': ['bank'],
            'technology': ['tech']
        }

        category = categorize_news_by_keywords(news_item, sector_keywords)
        assert category == 'general'

    def test_clean_text_for_telegram(self):
        """Test cleaning text for Telegram formatting"""
        text = """
        ╔══════════════════════════════════════╗
        ║           Test Report                ║
        ╚══════════════════════════════════════╝

        **Section Header**
        - Bullet point 1
        - Bullet point 2
        """

        result = clean_text_for_telegram(text)
        assert '╔' not in result
        assert '║' not in result
        assert '╚' not in result
        assert '**Section Header**' in result
        assert '- Bullet point 1' in result

    def test_format_telegram_section_header(self):
        """Test formatting section headers for Telegram"""
        # Test double asterisk headers
        result1 = format_telegram_section_header('**Key Trends**')
        assert result1 == '<b>KEY TRENDS</b>'

        # Test single asterisk headers
        result2 = format_telegram_section_header('*Important Note*')
        assert result2 == '<b>Important Note</b>'

        # Test regular text
        result3 = format_telegram_section_header('Regular text')
        assert result3 == 'Regular text'

    def test_format_telegram_bullet_points(self):
        """Test formatting bullet points for Telegram"""
        # Test dash bullet points
        result1 = format_telegram_bullet_points('- First point')
        assert result1 == '• First point'

        # Test numbered lists
        result2 = format_telegram_bullet_points('1. First item')
        assert result2 == '1. First item'

        # Test regular text
        result3 = format_telegram_bullet_points('Regular text')
        assert result3 == 'Regular text'

    def test_split_text_into_chunks_small_text(self):
        """Test splitting small text (no chunking needed)"""
        text = "Short text that doesn't need chunking"
        chunks = split_text_into_chunks(text, max_length=1000)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_split_text_into_chunks_large_text(self):
        """Test splitting large text into chunks"""
        # Create text larger than max_length
        sections = [f"Section {i}\n\nContent for section {i}" for i in range(1, 20)]
        text = "\n\n".join(sections)

        chunks = split_text_into_chunks(text, max_length=100)

        assert len(chunks) > 1
        # Verify all chunks are within size limit (with some tolerance for section boundaries)
        for chunk in chunks:
            assert len(chunk) <= 200  # Allow some tolerance for keeping sections together

    def test_split_text_into_chunks_preserves_content(self):
        """Test that chunking preserves all content"""
        text = "Section 1\n\nContent 1\n\nSection 2\n\nContent 2"
        chunks = split_text_into_chunks(text, max_length=50)

        reconstructed = "\n\n".join(chunks)
        assert "Section 1" in reconstructed
        assert "Content 1" in reconstructed
        assert "Section 2" in reconstructed
        assert "Content 2" in reconstructed

    def test_prepare_concise_batch_summary(self):
        """Test preparing concise batch summary"""
        news_data = [
            {
                'headline': 'Very long headline that should be truncated because it exceeds the character limit',
                'description': 'Very long description that should also be truncated because it exceeds the character limit for descriptions'
            },
            {
                'headline': 'Short headline',
                'description': 'Short description'
            }
        ]

        result = prepare_concise_batch_summary(news_data)

        assert '1.' in result
        assert '2.' in result
        # Check truncation occurred
        assert len(result.split('\n')[0]) <= 200  # First line should be reasonable length
        assert 'Short headline' in result
        assert 'Short description' in result

    def test_prepare_concise_batch_summary_empty_data(self):
        """Test preparing summary with empty data"""
        result = prepare_concise_batch_summary([])
        assert result == ""

    def test_prepare_concise_batch_summary_missing_fields(self):
        """Test preparing summary with missing fields"""
        news_data = [
            {'headline': 'Only headline'},
            {'description': 'Only description'},
            {}  # Empty item
        ]

        result = prepare_concise_batch_summary(news_data)

        assert '1. Only headline - ' in result
        assert '2.  - Only description' in result
        assert '3.  - ' in result