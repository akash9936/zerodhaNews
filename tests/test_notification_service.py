"""
Unit tests for notification_service module
"""
import pytest
from unittest.mock import patch, Mock
from notification_service import NotificationService


class TestNotificationService:

    @patch('notification_service.get_telegram_credentials')
    @patch('notification_service.TelegramBot')
    def test_init_with_credentials(self, mock_telegram_bot, mock_get_credentials):
        """Test service initialization with Telegram credentials"""
        mock_get_credentials.return_value = ("test_token", "test_chat_id")
        mock_bot_instance = Mock()
        mock_telegram_bot.return_value = mock_bot_instance

        service = NotificationService()

        assert service.telegram_token == "test_token"
        assert service.telegram_chat_id == "test_chat_id"
        assert service.telegram_bot == mock_bot_instance
        mock_telegram_bot.assert_called_once_with("test_token", "test_chat_id")

    @patch('notification_service.get_telegram_credentials')
    def test_init_without_credentials(self, mock_get_credentials):
        """Test service initialization without Telegram credentials"""
        mock_get_credentials.return_value = (None, None)

        service = NotificationService()

        assert service.telegram_token is None
        assert service.telegram_chat_id is None
        assert service.telegram_bot is None

    @patch('notification_service.get_telegram_credentials')
    def test_init_partial_credentials(self, mock_get_credentials):
        """Test service initialization with partial credentials"""
        mock_get_credentials.return_value = ("test_token", None)

        service = NotificationService()

        assert service.telegram_bot is None

    def test_is_telegram_enabled_true(self, mock_telegram_bot):
        """Test Telegram enabled check when bot is available"""
        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = ("token", "chat_id")
            with patch('notification_service.TelegramBot') as mock_bot_class:
                mock_bot_class.return_value = mock_telegram_bot

                service = NotificationService()
                assert service.is_telegram_enabled() is True

    def test_is_telegram_enabled_false(self):
        """Test Telegram enabled check when bot is not available"""
        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = (None, None)

            service = NotificationService()
            assert service.is_telegram_enabled() is False

    @patch('notification_service.split_text_into_chunks')
    def test_send_telegram_report_success_single_chunk(self, mock_split, sample_analysis_results):
        """Test sending Telegram report with single chunk"""
        mock_split.return_value = ["Single chunk content"]

        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = ("token", "chat_id")
            with patch('notification_service.TelegramBot') as mock_bot_class:
                mock_bot = Mock()
                mock_bot.send_message.return_value = True
                mock_bot_class.return_value = mock_bot

                service = NotificationService()
                mock_report_generator = Mock()
                mock_report_generator.generate_telegram_report_content.return_value = "Test content"

                result = service.send_telegram_report(sample_analysis_results, mock_report_generator)

                assert result is True
                mock_bot.send_message.assert_called_once()
                call_args = mock_bot.send_message.call_args
                assert "📊 Financial News Report" in call_args[0][0]
                assert call_args[1]['parse_mode'] == 'HTML'

    @patch('notification_service.split_text_into_chunks')
    def test_send_telegram_report_success_multiple_chunks(self, mock_split, sample_analysis_results):
        """Test sending Telegram report with multiple chunks"""
        mock_split.return_value = ["Chunk 1", "Chunk 2"]

        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = ("token", "chat_id")
            with patch('notification_service.TelegramBot') as mock_bot_class:
                mock_bot = Mock()
                mock_bot.send_message.return_value = True
                mock_bot_class.return_value = mock_bot

                service = NotificationService()
                mock_report_generator = Mock()
                mock_report_generator.generate_telegram_report_content.return_value = "Test content"

                result = service.send_telegram_report(sample_analysis_results, mock_report_generator)

                assert result is True
                assert mock_bot.send_message.call_count == 2

                # Check that part numbers are added
                first_call = mock_bot.send_message.call_args_list[0][0][0]
                second_call = mock_bot.send_message.call_args_list[1][0][0]
                assert "Part 1/2" in first_call
                assert "Part 2/2" in second_call

    def test_send_telegram_report_disabled(self, sample_analysis_results):
        """Test sending report when Telegram is disabled"""
        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = (None, None)

            service = NotificationService()
            mock_report_generator = Mock()

            result = service.send_telegram_report(sample_analysis_results, mock_report_generator)

            assert result is False

    @patch('notification_service.split_text_into_chunks')
    def test_send_telegram_report_partial_failure(self, mock_split, sample_analysis_results):
        """Test sending report with partial failure"""
        mock_split.return_value = ["Chunk 1", "Chunk 2"]

        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = ("token", "chat_id")
            with patch('notification_service.TelegramBot') as mock_bot_class:
                mock_bot = Mock()
                # First call succeeds, second fails
                mock_bot.send_message.side_effect = [True, False]
                mock_bot_class.return_value = mock_bot

                service = NotificationService()
                mock_report_generator = Mock()
                mock_report_generator.generate_telegram_report_content.return_value = "Test content"

                result = service.send_telegram_report(sample_analysis_results, mock_report_generator)

                assert result is False  # Should return False for partial failure

    @patch('notification_service.split_text_into_chunks')
    def test_send_telegram_report_exception(self, mock_split, sample_analysis_results):
        """Test sending report with exception"""
        mock_split.side_effect = Exception("Test exception")

        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = ("token", "chat_id")
            with patch('notification_service.TelegramBot') as mock_bot_class:
                mock_bot_class.return_value = Mock()

                service = NotificationService()
                mock_report_generator = Mock()
                mock_report_generator.generate_telegram_report_content.return_value = "Test content"

                result = service.send_telegram_report(sample_analysis_results, mock_report_generator)

                assert result is False

    def test_send_notification_enabled(self, sample_analysis_results):
        """Test sending notification when Telegram is enabled"""
        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = ("token", "chat_id")
            with patch('notification_service.TelegramBot') as mock_bot_class:
                mock_bot_class.return_value = Mock()

                service = NotificationService()

                with patch.object(service, 'send_telegram_report', return_value=True) as mock_send:
                    mock_report_generator = Mock()
                    results = service.send_notification(sample_analysis_results, mock_report_generator)

                    assert results['telegram'] is True
                    mock_send.assert_called_once_with(sample_analysis_results, mock_report_generator)

    def test_send_notification_disabled(self, sample_analysis_results):
        """Test sending notification when Telegram is disabled"""
        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = (None, None)

            service = NotificationService()
            mock_report_generator = Mock()

            results = service.send_notification(sample_analysis_results, mock_report_generator)

            assert results['telegram'] is False

    @patch('notification_service.split_text_into_chunks')
    def test_send_telegram_report_chunk_exception(self, mock_split, sample_analysis_results):
        """Test handling exception during chunk sending"""
        mock_split.return_value = ["Chunk 1", "Chunk 2"]

        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = ("token", "chat_id")
            with patch('notification_service.TelegramBot') as mock_bot_class:
                mock_bot = Mock()
                # First call succeeds, second raises exception
                mock_bot.send_message.side_effect = [True, Exception("Send error")]
                mock_bot_class.return_value = mock_bot

                service = NotificationService()
                mock_report_generator = Mock()
                mock_report_generator.generate_telegram_report_content.return_value = "Test content"

                result = service.send_telegram_report(sample_analysis_results, mock_report_generator)

                assert result is False  # Should return False when any chunk fails

    @patch('notification_service.split_text_into_chunks')
    def test_send_telegram_report_empty_chunks(self, mock_split, sample_analysis_results):
        """Test sending report with empty chunks"""
        mock_split.return_value = []

        with patch('notification_service.get_telegram_credentials') as mock_creds:
            mock_creds.return_value = ("token", "chat_id")
            with patch('notification_service.TelegramBot') as mock_bot_class:
                mock_bot = Mock()
                mock_bot_class.return_value = mock_bot

                service = NotificationService()
                mock_report_generator = Mock()
                mock_report_generator.generate_telegram_report_content.return_value = "Test content"

                result = service.send_telegram_report(sample_analysis_results, mock_report_generator)

                assert result is True  # Should succeed with no chunks to send
                mock_bot.send_message.assert_not_called()