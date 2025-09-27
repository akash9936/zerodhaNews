"""
Integration tests for pipeline_orchestrator module
"""
import pytest
import os
from unittest.mock import patch, Mock
from pipeline_orchestrator import NewsAnalysisPipeline


class TestNewsAnalysisPipeline:

    @patch('pipeline_orchestrator.load_dotenv')
    @patch('pipeline_orchestrator.os.makedirs')
    def test_init(self, mock_makedirs, mock_load_dotenv):
        """Test pipeline initialization"""
        with patch('pipeline_orchestrator.ZerodhaPulseScraper') as mock_scraper, \
             patch('pipeline_orchestrator.NewsAnalyzer') as mock_analyzer, \
             patch('pipeline_orchestrator.ReportGenerator') as mock_report_gen, \
             patch('pipeline_orchestrator.NotificationService') as mock_notification:

            pipeline = NewsAnalysisPipeline()

            mock_load_dotenv.assert_called_once()
            mock_makedirs.assert_called_once_with('data', exist_ok=True)
            mock_scraper.assert_called_once()
            mock_analyzer.assert_called_once()
            mock_report_gen.assert_called_once()
            mock_notification.assert_called_once()

    def test_run_complete_pipeline_success(self, sample_news_data, sample_analysis_results):
        """Test successful complete pipeline run"""
        with patch('pipeline_orchestrator.ZerodhaPulseScraper') as mock_scraper_class, \
             patch('pipeline_orchestrator.NewsAnalyzer') as mock_analyzer_class, \
             patch('pipeline_orchestrator.ReportGenerator') as mock_report_gen_class, \
             patch('pipeline_orchestrator.NotificationService') as mock_notification_class, \
             patch('pipeline_orchestrator.load_dotenv'), \
             patch('pipeline_orchestrator.os.makedirs'):

            # Setup mocks
            mock_scraper = Mock()
            mock_scraper.scrape_news.return_value = sample_news_data
            mock_scraper.save_news_data.return_value = "test_file.json"
            mock_scraper_class.return_value = mock_scraper

            mock_analyzer = Mock()
            mock_analyzer.analyze_all_news_consolidated.return_value = sample_analysis_results
            mock_analyzer_class.return_value = mock_analyzer

            mock_report_gen = Mock()
            mock_report_gen.generate_clean_daily_report.return_value = "Test report"
            mock_report_gen.get_report_filename.return_value = "test_report.txt"
            mock_report_gen.save_report.return_value = "test_report.txt"
            mock_report_gen_class.return_value = mock_report_gen

            mock_notification = Mock()
            mock_notification.send_notification.return_value = {'telegram': True}
            mock_notification_class.return_value = mock_notification

            pipeline = NewsAnalysisPipeline()
            result = pipeline.run_complete_pipeline()

            # Verify success
            assert result['success'] is True
            assert result['news_items_scraped'] == len(sample_news_data)
            assert result['analysis_results'] == sample_analysis_results
            assert result['report_file'] == "test_report.txt"
            assert result['notification_results'] == {'telegram': True}
            assert 'start_time' in result
            assert 'end_time' in result
            assert 'duration_seconds' in result

            # Verify method calls
            mock_scraper.scrape_news.assert_called_once()
            mock_scraper.save_news_data.assert_called_once_with(sample_news_data)
            mock_analyzer.analyze_all_news_consolidated.assert_called_once_with(sample_news_data)
            mock_report_gen.generate_clean_daily_report.assert_called_once_with(sample_analysis_results)
            mock_notification.send_notification.assert_called_once()

    def test_run_complete_pipeline_scraping_failure(self):
        """Test pipeline with scraping failure"""
        with patch('pipeline_orchestrator.ZerodhaPulseScraper') as mock_scraper_class, \
             patch('pipeline_orchestrator.load_dotenv'), \
             patch('pipeline_orchestrator.os.makedirs'):

            mock_scraper = Mock()
            mock_scraper.scrape_news.return_value = None  # Scraping fails
            mock_scraper_class.return_value = mock_scraper

            pipeline = NewsAnalysisPipeline()
            result = pipeline.run_complete_pipeline()

            assert result['success'] is False
            assert result['error'] == 'Failed to scrape news'
            assert 'start_time' in result
            assert 'end_time' in result

    def test_run_complete_pipeline_report_save_failure(self, sample_news_data, sample_analysis_results):
        """Test pipeline with report saving failure"""
        with patch('pipeline_orchestrator.ZerodhaPulseScraper') as mock_scraper_class, \
             patch('pipeline_orchestrator.NewsAnalyzer') as mock_analyzer_class, \
             patch('pipeline_orchestrator.ReportGenerator') as mock_report_gen_class, \
             patch('pipeline_orchestrator.NotificationService') as mock_notification_class, \
             patch('pipeline_orchestrator.load_dotenv'), \
             patch('pipeline_orchestrator.os.makedirs'):

            # Setup mocks
            mock_scraper = Mock()
            mock_scraper.scrape_news.return_value = sample_news_data
            mock_scraper.save_news_data.return_value = "test_file.json"
            mock_scraper_class.return_value = mock_scraper

            mock_analyzer = Mock()
            mock_analyzer.analyze_all_news_consolidated.return_value = sample_analysis_results
            mock_analyzer_class.return_value = mock_analyzer

            mock_report_gen = Mock()
            mock_report_gen.generate_clean_daily_report.return_value = "Test report"
            mock_report_gen.get_report_filename.return_value = "test_report.txt"
            mock_report_gen.save_report.return_value = None  # Save fails
            mock_report_gen_class.return_value = mock_report_gen

            mock_notification = Mock()
            mock_notification_class.return_value = mock_notification

            pipeline = NewsAnalysisPipeline()
            result = pipeline.run_complete_pipeline()

            # Should still succeed but with empty notification results
            assert result['success'] is True
            assert result['report_file'] is None
            assert result['notification_results'] == {}

    def test_run_complete_pipeline_exception(self):
        """Test pipeline with unexpected exception"""
        with patch('pipeline_orchestrator.load_dotenv'), \
             patch('pipeline_orchestrator.os.makedirs'):

            # Mock the scraper to raise exception during scrape_news call
            with patch('pipeline_orchestrator.ZerodhaPulseScraper') as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper.scrape_news.side_effect = Exception("Unexpected error")
                mock_scraper_class.return_value = mock_scraper

                pipeline = NewsAnalysisPipeline()
                result = pipeline.run_complete_pipeline()

                assert result['success'] is False
                assert "Unexpected error" in result['error']
                assert 'start_time' in result
                assert 'end_time' in result

    def test_log_completion_summary(self, sample_analysis_results):
        """Test logging completion summary"""
        pipeline_results = {
            'success': True,
            'analysis_results': sample_analysis_results,
            'duration_seconds': 45.67,
            'report_file': 'test_report.txt',
            'notification_results': {'telegram': True},
            'start_time': '2025-01-01T12:00:00'
        }

        with patch('pipeline_orchestrator.load_dotenv'), \
             patch('pipeline_orchestrator.os.makedirs'), \
             patch('pipeline_orchestrator.logger') as mock_logger:

            pipeline = NewsAnalysisPipeline()
            pipeline._log_completion_summary(pipeline_results)

            # Verify logging calls
            assert mock_logger.info.call_count >= 5
            log_messages = [call[0][0] for call in mock_logger.info.call_args_list]

            # Check key information is logged
            assert any("Analysis complete!" in msg for msg in log_messages)
            assert any("45.67 seconds" in msg for msg in log_messages)
            assert any("4 API calls" in msg for msg in log_messages)
            assert any("50 news items" in msg for msg in log_messages)
            assert any("test_report.txt" in msg for msg in log_messages)

    def test_display_report(self):
        """Test report display"""
        with patch('pipeline_orchestrator.load_dotenv'), \
             patch('pipeline_orchestrator.os.makedirs'), \
             patch('builtins.print') as mock_print:

            pipeline = NewsAnalysisPipeline()
            test_report = "Test report content"

            pipeline.display_report(test_report)

            # Verify print calls
            assert mock_print.call_count >= 3
            print_args = [call[0][0] for call in mock_print.call_args_list]

            assert "=" * 80 in print_args
            assert test_report in print_args

    def test_run_pipeline_with_display_success(self, sample_news_data, sample_analysis_results):
        """Test pipeline with display - success case"""
        with patch('pipeline_orchestrator.ZerodhaPulseScraper') as mock_scraper_class, \
             patch('pipeline_orchestrator.NewsAnalyzer') as mock_analyzer_class, \
             patch('pipeline_orchestrator.ReportGenerator') as mock_report_gen_class, \
             patch('pipeline_orchestrator.NotificationService') as mock_notification_class, \
             patch('pipeline_orchestrator.load_dotenv'), \
             patch('pipeline_orchestrator.os.makedirs'), \
             patch('builtins.print'):

            # Setup successful mocks
            mock_scraper = Mock()
            mock_scraper.scrape_news.return_value = sample_news_data
            mock_scraper.save_news_data.return_value = "test_file.json"
            mock_scraper_class.return_value = mock_scraper

            mock_analyzer = Mock()
            mock_analyzer.analyze_all_news_consolidated.return_value = sample_analysis_results
            mock_analyzer_class.return_value = mock_analyzer

            mock_report_gen = Mock()
            mock_report_gen.generate_clean_daily_report.return_value = "Test report"
            mock_report_gen.get_report_filename.return_value = "test_report.txt"
            mock_report_gen.save_report.return_value = "test_report.txt"
            mock_report_gen_class.return_value = mock_report_gen

            mock_notification = Mock()
            mock_notification.send_notification.return_value = {'telegram': True}
            mock_notification_class.return_value = mock_notification

            pipeline = NewsAnalysisPipeline()
            result = pipeline.run_pipeline_with_display()

            assert result['success'] is True

    def test_run_pipeline_with_display_failure(self):
        """Test pipeline with display - failure case"""
        with patch('pipeline_orchestrator.ZerodhaPulseScraper') as mock_scraper_class, \
             patch('pipeline_orchestrator.load_dotenv'), \
             patch('pipeline_orchestrator.os.makedirs'):

            mock_scraper = Mock()
            mock_scraper.scrape_news.return_value = None
            mock_scraper_class.return_value = mock_scraper

            pipeline = NewsAnalysisPipeline()
            result = pipeline.run_pipeline_with_display()

            assert result['success'] is False


class TestMainFunction:

    @patch('pipeline_orchestrator.NewsAnalysisPipeline')
    def test_main_success(self, mock_pipeline_class):
        """Test main function success"""
        from pipeline_orchestrator import main

        mock_pipeline = Mock()
        mock_pipeline.run_pipeline_with_display.return_value = {'success': True}
        mock_pipeline_class.return_value = mock_pipeline

        result = main()

        assert result == 0
        mock_pipeline.run_pipeline_with_display.assert_called_once()

    @patch('pipeline_orchestrator.NewsAnalysisPipeline')
    def test_main_failure(self, mock_pipeline_class):
        """Test main function failure"""
        from pipeline_orchestrator import main

        mock_pipeline = Mock()
        mock_pipeline.run_pipeline_with_display.return_value = {'success': False}
        mock_pipeline_class.return_value = mock_pipeline

        result = main()

        assert result == 1

    @patch('pipeline_orchestrator.NewsAnalysisPipeline')
    def test_main_keyboard_interrupt(self, mock_pipeline_class):
        """Test main function with keyboard interrupt"""
        from pipeline_orchestrator import main

        mock_pipeline_class.side_effect = KeyboardInterrupt()

        result = main()

        assert result == 0

    @patch('pipeline_orchestrator.NewsAnalysisPipeline')
    def test_main_exception(self, mock_pipeline_class):
        """Test main function with exception"""
        from pipeline_orchestrator import main

        mock_pipeline_class.side_effect = Exception("Test error")

        result = main()

        assert result == 1