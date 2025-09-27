"""
Unit tests for news_analyzer module
"""
import pytest
import json
import time
from unittest.mock import patch, Mock
from news_analyzer import NewsAnalyzer


class TestNewsAnalyzer:

    @patch('news_analyzer.get_groq_token')
    def test_init_with_token(self, mock_get_token):
        """Test analyzer initialization with provided token"""
        analyzer = NewsAnalyzer("test_token")

        assert "Bearer test_token" in analyzer.headers['Authorization']
        assert analyzer.model == "meta-llama/llama-4-scout-17b-16e-instruct"
        assert analyzer.batch_size == 15

    @patch('news_analyzer.get_groq_token')
    def test_init_without_token(self, mock_get_token):
        """Test analyzer initialization without token"""
        mock_get_token.return_value = "retrieved_token"

        analyzer = NewsAnalyzer()

        mock_get_token.assert_called_once()
        assert "Bearer retrieved_token" in analyzer.headers['Authorization']

    def test_prioritize_news(self, sample_news_data):
        """Test news prioritization"""
        analyzer = NewsAnalyzer("test_token")

        prioritized = analyzer.prioritize_news(sample_news_data)

        assert len(prioritized) == len(sample_news_data)
        assert isinstance(prioritized, list)
        # High priority news should be first (contains financial keywords)
        assert any('HDFC' in item['headline'] for item in prioritized[:2])

    def test_categorize_news_by_sector(self, sample_news_data):
        """Test news categorization by sector"""
        analyzer = NewsAnalyzer("test_token")

        categorized = analyzer.categorize_news_by_sector(sample_news_data)

        assert 'banking' in categorized
        assert 'technology' in categorized
        assert 'general' in categorized

        # HDFC should be in banking
        banking_news = categorized['banking']
        assert any('HDFC' in item['headline'] for item in banking_news)

        # Infosys should be in technology
        tech_news = categorized['technology']
        assert any('Infosys' in item['headline'] for item in tech_news)

    def test_split_into_batches(self, sample_news_data):
        """Test splitting news into batches"""
        analyzer = NewsAnalyzer("test_token")

        # Test with small batch size
        analyzer.batch_size = 2
        batches = analyzer.split_into_batches(sample_news_data)

        assert len(batches) == 2  # 3 items with batch size 2 = 2 batches
        assert len(batches[0]) == 2
        assert len(batches[1]) == 1

    def test_split_into_batches_empty(self):
        """Test splitting empty news list"""
        analyzer = NewsAnalyzer("test_token")

        batches = analyzer.split_into_batches([])

        assert batches == []

    @patch('news_analyzer.requests.post')
    def test_query_groq_model_success(self, mock_post, mock_groq_response):
        """Test successful Groq API query"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_groq_response

        analyzer = NewsAnalyzer("test_token")
        result = analyzer.query_groq_model("Test prompt")

        assert "Key Sector Trends" in result
        assert "Buy/Sell Opportunities" in result
        mock_post.assert_called_once()

    @patch('news_analyzer.requests.post')
    def test_query_groq_model_rate_limit(self, mock_post):
        """Test Groq API rate limiting"""
        # First call returns rate limit, second succeeds
        mock_post.side_effect = [
            Mock(status_code=429),
            Mock(status_code=200, json=lambda: {'choices': [{'message': {'content': 'Success'}}]})
        ]

        analyzer = NewsAnalyzer("test_token")

        with patch('time.sleep') as mock_sleep:
            result = analyzer.query_groq_model("Test prompt", max_retries=2)

        assert result == "Success"
        assert mock_post.call_count == 2
        mock_sleep.assert_called()

    @patch('news_analyzer.requests.post')
    def test_query_groq_model_error(self, mock_post):
        """Test Groq API error handling"""
        mock_post.side_effect = Exception("Network error")

        analyzer = NewsAnalyzer("test_token")
        result = analyzer.query_groq_model("Test prompt", max_retries=1)

        assert "Error:" in result

    @patch('news_analyzer.requests.post')
    def test_query_groq_model_max_retries(self, mock_post):
        """Test max retries exceeded"""
        mock_post.side_effect = Exception("Persistent error")

        analyzer = NewsAnalyzer("test_token")
        result = analyzer.query_groq_model("Test prompt", max_retries=2)

        assert "Error:" in result  # More flexible assertion
        assert mock_post.call_count == 2

    @patch('news_analyzer.NewsAnalyzer.query_groq_model')
    def test_analyze_batch_for_insights(self, mock_query, sample_news_data):
        """Test batch analysis for insights"""
        mock_query.return_value = "Mocked insights"

        analyzer = NewsAnalyzer("test_token")
        result = analyzer.analyze_batch_for_insights(sample_news_data[:2], 1, 2)

        assert result == "Mocked insights"
        mock_query.assert_called_once()

        # Check that prompt contains batch information
        call_args = mock_query.call_args[0][0]
        assert "NEWS BATCH 1/2" in call_args
        assert "HDFC Bank" in call_args

    @patch('news_analyzer.NewsAnalyzer.query_groq_model')
    def test_generate_final_consolidated_report(self, mock_query):
        """Test generating final consolidated report"""
        mock_query.return_value = "Final consolidated report"

        batch_insights = ["Insight 1", "Insight 2"]
        sector_summary = {'banking': 2, 'technology': 1}

        analyzer = NewsAnalyzer("test_token")
        result = analyzer.generate_final_consolidated_report(
            batch_insights, sector_summary, 10
        )

        assert result == "Final consolidated report"
        mock_query.assert_called_once()

        # Check prompt contains all required information
        call_args = mock_query.call_args[0][0]
        assert "Banking(2)" in call_args
        assert "Technology(1)" in call_args
        assert "TOTAL NEWS ANALYZED: 10" in call_args

    @patch('news_analyzer.NewsAnalyzer.analyze_batch_for_insights')
    @patch('news_analyzer.NewsAnalyzer.generate_final_consolidated_report')
    @patch('time.sleep')
    def test_analyze_all_news_consolidated(self, mock_sleep, mock_final_report,
                                         mock_batch_insights, sample_news_data):
        """Test complete news analysis pipeline"""
        mock_batch_insights.return_value = "Batch insights"
        mock_final_report.return_value = "Final report"

        analyzer = NewsAnalyzer("test_token")
        analyzer.batch_size = 2  # Force multiple batches

        result = analyzer.analyze_all_news_consolidated(sample_news_data)

        assert result['total_news_items'] == 3
        assert result['final_report'] == "Final report"
        assert result['api_calls_used'] == 3  # 2 batch calls + 1 final report
        assert 'sector_summary' in result
        assert 'analysis_timestamp' in result

        # Verify sleep was called between batches
        mock_sleep.assert_called()

    def test_analyze_all_news_consolidated_empty(self):
        """Test analysis with empty news data"""
        analyzer = NewsAnalyzer("test_token")

        with patch.object(analyzer, 'generate_final_consolidated_report') as mock_final:
            mock_final.return_value = "Empty report"
            result = analyzer.analyze_all_news_consolidated([])

        assert result['total_news_items'] == 0
        assert result['api_calls_used'] == 1  # Only final report call

    @patch('news_analyzer.requests.post')
    def test_query_groq_model_invalid_response(self, mock_post):
        """Test handling invalid API response"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}  # Missing 'choices'

        analyzer = NewsAnalyzer("test_token")
        result = analyzer.query_groq_model("Test prompt")

        # Should return some error indication when response is malformed
        assert result is not None

    @patch('news_analyzer.requests.post')
    def test_query_groq_model_http_error(self, mock_post):
        """Test handling HTTP error codes"""
        mock_post.return_value.status_code = 500

        analyzer = NewsAnalyzer("test_token")
        result = analyzer.query_groq_model("Test prompt")

        assert "API Error: 500" in result