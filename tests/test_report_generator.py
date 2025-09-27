"""
Unit tests for report_generator module
"""
import pytest
import os
from unittest.mock import patch, mock_open, Mock
from report_generator import ReportGenerator


class TestReportGenerator:

    def test_init(self):
        """Test report generator initialization"""
        generator = ReportGenerator()
        assert generator.data_dir == 'data'
        assert generator.encoding == 'utf-8'

    def test_generate_clean_daily_report(self, sample_analysis_results):
        """Test generating clean daily report"""
        generator = ReportGenerator()

        with patch('report_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-01-01 12:00:00"

            report = generator.generate_clean_daily_report(sample_analysis_results)

            assert "📈 STRUCTURED FINANCIAL NEWS REPORT 📈" in report
            assert "2025-01-01 12:00:00" in report
            assert "50 news items analyzed" in report
            assert "Banking: 10" in report
            assert "Technology: 8" in report
            assert "4 AI analysis calls" in report
            assert sample_analysis_results['final_report'] in report

    def test_generate_clean_daily_report_empty_sectors(self):
        """Test report generation with empty sectors"""
        results = {
            'total_news_items': 5,
            'sector_summary': {'banking': 0, 'technology': 5, 'general': 0},
            'final_report': 'Test report content',
            'api_calls_used': 2
        }

        generator = ReportGenerator()

        with patch('report_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-01-01 12:00:00"

            report = generator.generate_clean_daily_report(results)

            # Should only include sectors with count > 0
            assert "Technology: 5" in report
            assert "Banking: 0" not in report
            assert "General: 0" not in report

    @patch('report_generator.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('report_generator.format_timestamp')
    def test_save_report_with_filename(self, mock_timestamp, mock_file, mock_makedirs):
        """Test saving report with provided filename"""
        generator = ReportGenerator()
        report_content = "Test report content"
        filename = "/custom/path/report.txt"

        result = generator.save_report(report_content, filename)

        assert result == filename
        mock_makedirs.assert_called_once_with('data', exist_ok=True)
        mock_file.assert_called_once_with(filename, 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with(report_content)

    @patch('report_generator.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('report_generator.format_timestamp')
    def test_save_report_auto_filename(self, mock_timestamp, mock_file, mock_makedirs):
        """Test saving report with auto-generated filename"""
        mock_timestamp.return_value = "2025-01-01_12-00-00"

        generator = ReportGenerator()
        report_content = "Test report content"

        result = generator.save_report(report_content)

        expected_filename = "data/zerodha_news_report_2025-01-01_12-00-00.txt"
        assert result == expected_filename
        mock_file.assert_called_once_with(expected_filename, 'w', encoding='utf-8')

    @patch('report_generator.os.makedirs')
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_save_report_error(self, mock_file, mock_makedirs):
        """Test saving report with file error"""
        generator = ReportGenerator()

        result = generator.save_report("Test content", "test.txt")

        assert result is None

    def test_generate_telegram_report_content(self, sample_analysis_results):
        """Test generating Telegram-optimized report content"""
        generator = ReportGenerator()

        with patch('utils.time_utils.get_ist_time') as mock_ist:
            mock_ist.return_value.strftime.return_value = "2025-01-01 12:00:00"

            content = generator.generate_telegram_report_content(sample_analysis_results)

            assert "<b>📊 FINANCIAL NEWS REPORT</b>" in content
            assert "2025-01-01 12:00:00 IST" in content
            assert "<b>Analysis Information</b>" in content
            assert "Total News Items Analyzed: 50" in content
            assert "AI Analysis Calls: 4" in content

    def test_generate_telegram_report_content_formatting(self):
        """Test Telegram content formatting"""
        results = {
            'total_news_items': 10,
            'final_report': """**Key Trends** 🌍📈
- Banking sector showing growth
*Important Note*
- Technology stocks rising""",
            'api_calls_used': 2
        }

        generator = ReportGenerator()

        with patch('utils.time_utils.get_ist_time') as mock_ist:
            mock_ist.return_value.strftime.return_value = "2025-01-01 12:00:00"

            content = generator.generate_telegram_report_content(results)

            assert "<b>KEY TRENDS</b>" in content  # ** formatting
            assert "<b>Important Note</b>" in content  # * formatting
            assert "• Banking sector showing growth" in content  # - to • conversion

    def test_format_report_summary(self, sample_analysis_results):
        """Test formatting report summary"""
        generator = ReportGenerator()

        summary = generator.format_report_summary(sample_analysis_results)

        assert "✅ Analysis complete!" in summary
        assert "📈 Key Sector Trends" in summary
        assert "💰 Buy/Sell Opportunities" in summary
        assert "🏦 Macro Implications" in summary
        assert "🏢 Corporate Actions" in summary
        assert "4 API calls" in summary
        assert "50 news items" in summary

    @patch('report_generator.format_timestamp')
    def test_get_report_filename_with_timestamp(self, mock_timestamp):
        """Test getting report filename with provided timestamp"""
        mock_timestamp.return_value = "2025-01-01_12-00-00"

        generator = ReportGenerator()
        filename = generator.get_report_filename("custom_timestamp")

        assert filename == "data/zerodha_news_report_custom_timestamp.txt"
        # Should not call format_timestamp when timestamp is provided
        mock_timestamp.assert_not_called()

    @patch('report_generator.format_timestamp')
    def test_get_report_filename_auto_timestamp(self, mock_timestamp):
        """Test getting report filename with auto-generated timestamp"""
        mock_timestamp.return_value = "2025-01-01_12-00-00"

        generator = ReportGenerator()
        filename = generator.get_report_filename()

        assert filename == "data/zerodha_news_report_2025-01-01_12-00-00.txt"
        mock_timestamp.assert_called_once()

    def test_generate_telegram_report_empty_content(self):
        """Test generating Telegram content with minimal data"""
        results = {
            'total_news_items': 0,
            'final_report': "",
            'api_calls_used': 0
        }

        generator = ReportGenerator()

        with patch('utils.time_utils.get_ist_time') as mock_ist:
            mock_ist.return_value.strftime.return_value = "2025-01-01 12:00:00"

            content = generator.generate_telegram_report_content(results)

            assert "<b>📊 FINANCIAL NEWS REPORT</b>" in content
            assert "Total News Items Analyzed: 0" in content
            assert "AI Analysis Calls: 0" in content

    def test_generate_clean_daily_report_special_characters(self):
        """Test report generation with special characters"""
        results = {
            'total_news_items': 1,
            'sector_summary': {'banking': 1},
            'final_report': 'Report with émojis 📈 and special chars ₹',
            'api_calls_used': 1
        }

        generator = ReportGenerator()

        with patch('report_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-01-01 12:00:00"

            report = generator.generate_clean_daily_report(results)

            assert 'émojis 📈' in report
            assert '₹' in report