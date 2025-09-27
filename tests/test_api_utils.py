"""
Unit tests for api_utils module
"""
import pytest
import os
from unittest.mock import patch, mock_open, Mock
from utils.api_utils import (
    get_groq_token,
    get_telegram_credentials,
    check_safari_setup
)


class TestApiUtils:

    @patch('utils.api_utils.load_dotenv')
    @patch.dict(os.environ, {'GROQ_API_KEY': 'gsk_test_token_123'})
    def test_get_groq_token_valid_env(self, mock_load_dotenv):
        """Test getting valid Groq token from environment"""
        result = get_groq_token()
        assert result == 'gsk_test_token_123'
        mock_load_dotenv.assert_called_once()

    @patch('utils.api_utils.load_dotenv')
    @patch.dict(os.environ, {'GROQ_API_KEY': 'invalid_token'})
    @patch('builtins.input', return_value='gsk_valid_token_456')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_groq_token_invalid_env_valid_input(self, mock_file, mock_input, mock_load_dotenv):
        """Test getting token from user input when env token is invalid"""
        result = get_groq_token()

        assert result == 'gsk_valid_token_456'
        mock_input.assert_called_once()
        mock_file.assert_called_once_with('.env', 'a')
        mock_file().write.assert_called_once_with('\nGROQ_API_KEY=gsk_valid_token_456')

    @patch('utils.api_utils.load_dotenv')
    @patch.dict(os.environ, {}, clear=True)  # No GROQ_API_KEY
    @patch('builtins.input', return_value='invalid_format')
    def test_get_groq_token_invalid_input(self, mock_input, mock_load_dotenv):
        """Test handling invalid token format from user input"""
        result = get_groq_token()

        assert result is None
        mock_input.assert_called_once()

    @patch('utils.api_utils.load_dotenv')
    @patch.dict(os.environ, {}, clear=True)
    @patch('builtins.input', return_value='')
    def test_get_groq_token_empty_input(self, mock_input, mock_load_dotenv):
        """Test handling empty user input"""
        result = get_groq_token()

        assert result is None
        mock_input.assert_called_once()

    @patch('utils.api_utils.load_dotenv')
    @patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_bot_token',
        'TELEGRAM_CHAT_ID': 'test_chat_id'
    })
    def test_get_telegram_credentials_valid(self, mock_load_dotenv):
        """Test getting valid Telegram credentials"""
        token, chat_id = get_telegram_credentials()

        assert token == 'test_bot_token'
        assert chat_id == 'test_chat_id'
        mock_load_dotenv.assert_called_once()

    @patch('utils.api_utils.load_dotenv')
    @patch.dict(os.environ, {}, clear=True)
    def test_get_telegram_credentials_missing(self, mock_load_dotenv):
        """Test getting Telegram credentials when not set"""
        token, chat_id = get_telegram_credentials()

        assert token is None
        assert chat_id is None
        mock_load_dotenv.assert_called_once()

    @patch('utils.api_utils.load_dotenv')
    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})  # Missing chat_id
    def test_get_telegram_credentials_partial(self, mock_load_dotenv):
        """Test getting partial Telegram credentials"""
        token, chat_id = get_telegram_credentials()

        assert token == 'test_token'
        assert chat_id is None
        mock_load_dotenv.assert_called_once()

    @patch('builtins.print')
    @patch('builtins.input', return_value='')
    def test_check_safari_setup(self, mock_input, mock_print):
        """Test Safari setup check function"""
        check_safari_setup()

        # Verify it prints the setup instructions
        assert mock_print.call_count >= 5  # Should print multiple instruction lines
        mock_input.assert_called_once()

        # Check that important setup instructions are printed
        printed_text = ' '.join([str(call[0][0]) for call in mock_print.call_args_list])
        assert 'Safari' in printed_text
        assert 'Develop menu' in printed_text
        assert 'Remote Automation' in printed_text

    @patch('builtins.print')
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_check_safari_setup_keyboard_interrupt(self, mock_input, mock_print):
        """Test Safari setup check with keyboard interrupt"""
        with pytest.raises(KeyboardInterrupt):
            check_safari_setup()

        mock_input.assert_called_once()

    @patch('utils.api_utils.load_dotenv')
    @patch.dict(os.environ, {'GROQ_API_KEY': 'gsk_test'})
    @patch('builtins.input', return_value='gsk_new_token')
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_get_groq_token_file_write_error(self, mock_file, mock_input, mock_load_dotenv):
        """Test handling file write error when saving token"""
        # This should still return the token even if saving fails
        result = get_groq_token()

        # Should return the environment token since it's valid
        assert result == 'gsk_test'