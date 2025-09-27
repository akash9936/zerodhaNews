"""
Unit tests for time_utils module
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from utils.time_utils import (
    get_ist_time,
    parse_news_time,
    is_within_last_12_hours,
    format_timestamp,
    format_json_timestamp
)


class TestTimeUtils:

    def test_get_ist_time(self):
        """Test IST time calculation"""
        with patch('utils.time_utils.datetime') as mock_datetime:
            mock_utc_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_utc_time

            ist_time = get_ist_time()
            expected_time = mock_utc_time + timedelta(hours=5, minutes=30)

            assert ist_time == expected_time

    def test_parse_news_time_today(self):
        """Test parsing 'Today' format"""
        with patch('utils.time_utils.get_ist_time') as mock_ist:
            mock_ist.return_value = datetime(2025, 1, 1, 15, 0, 0)

            result = parse_news_time("Today, 10:30 AM")
            expected = datetime(2025, 1, 1, 10, 30, 0)

            assert result == expected

    def test_parse_news_time_yesterday(self):
        """Test parsing 'Yesterday' format"""
        with patch('utils.time_utils.get_ist_time') as mock_ist:
            mock_ist.return_value = datetime(2025, 1, 2, 15, 0, 0)

            result = parse_news_time("Yesterday, 2:15 PM")
            expected = datetime(2025, 1, 1, 14, 15, 0)

            assert result == expected

    def test_parse_news_time_specific_date(self):
        """Test parsing specific date format"""
        result = parse_news_time("26 May 2025, 11:45 AM")
        expected = datetime(2025, 5, 26, 11, 45, 0) + timedelta(hours=5, minutes=30)

        assert result == expected

    def test_parse_news_time_unknown(self):
        """Test parsing unknown time"""
        with patch('utils.time_utils.get_ist_time') as mock_ist:
            mock_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_ist.return_value = mock_time

            result = parse_news_time("Unknown time")
            assert result == mock_time

    def test_parse_news_time_empty(self):
        """Test parsing empty time string"""
        with patch('utils.time_utils.get_ist_time') as mock_ist:
            mock_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_ist.return_value = mock_time

            result = parse_news_time("")
            assert result == mock_time

    def test_parse_news_time_invalid_format(self):
        """Test parsing invalid time format"""
        with patch('utils.time_utils.get_ist_time') as mock_ist:
            mock_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_ist.return_value = mock_time

            result = parse_news_time("Invalid format")
            assert result == mock_time

    def test_is_within_last_12_hours_true(self):
        """Test time within last 12 hours"""
        with patch('utils.time_utils.get_ist_time') as mock_ist, \
             patch('utils.time_utils.parse_news_time') as mock_parse:

            current_time = datetime(2025, 1, 1, 12, 0, 0)
            news_time = datetime(2025, 1, 1, 6, 0, 0)  # 6 hours ago

            mock_ist.return_value = current_time
            mock_parse.return_value = news_time

            result = is_within_last_12_hours("6 hours ago")
            assert result is True

    def test_is_within_last_12_hours_false(self):
        """Test time not within last 12 hours"""
        with patch('utils.time_utils.get_ist_time') as mock_ist, \
             patch('utils.time_utils.parse_news_time') as mock_parse:

            current_time = datetime(2025, 1, 1, 12, 0, 0)
            news_time = datetime(2024, 12, 31, 12, 0, 0)  # 24 hours ago

            mock_ist.return_value = current_time
            mock_parse.return_value = news_time

            result = is_within_last_12_hours("24 hours ago")
            assert result is False

    def test_is_within_last_12_hours_error(self):
        """Test error handling in time check"""
        with patch('utils.time_utils.parse_news_time', side_effect=Exception("Test error")):
            result = is_within_last_12_hours("invalid")
            assert result is False

    def test_format_timestamp_default(self):
        """Test default timestamp formatting"""
        with patch('utils.time_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 30, 45)

            result = format_timestamp()
            assert result == "2025-01-01_12-30-45"

    def test_format_timestamp_custom(self):
        """Test custom timestamp formatting"""
        with patch('utils.time_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 30, 45)

            result = format_timestamp("%Y%m%d")
            assert result == "20250101"

    def test_format_json_timestamp(self):
        """Test JSON timestamp formatting"""
        with patch('utils.time_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 30, 45)

            result = format_json_timestamp()
            assert result == "20250101_123045"