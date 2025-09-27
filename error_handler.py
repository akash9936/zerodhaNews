"""
Centralized error handling and custom exceptions
"""
import logging
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)


class NewsAnalyzerError(Exception):
    """Base exception for news analyzer errors"""
    pass


class ScrapingError(NewsAnalyzerError):
    """Exception raised when scraping fails"""
    pass


class AnalysisError(NewsAnalyzerError):
    """Exception raised when analysis fails"""
    pass


class ReportGenerationError(NewsAnalyzerError):
    """Exception raised when report generation fails"""
    pass


class NotificationError(NewsAnalyzerError):
    """Exception raised when notifications fail"""
    pass


def handle_errors(error_type: type = NewsAnalyzerError, return_value: Any = None):
    """Decorator for handling errors with logging"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                return return_value
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                return return_value
        return wrapper
    return decorator


class ErrorHandler:
    """Centralized error handling utilities"""

    @staticmethod
    def log_and_return_none(func_name: str, error: Exception) -> None:
        """Log error and return None"""
        logger.error(f"Error in {func_name}: {str(error)}")
        return None

    @staticmethod
    def log_and_return_empty_list(func_name: str, error: Exception) -> list:
        """Log error and return empty list"""
        logger.error(f"Error in {func_name}: {str(error)}")
        return []

    @staticmethod
    def log_and_return_empty_dict(func_name: str, error: Exception) -> dict:
        """Log error and return empty dict"""
        logger.error(f"Error in {func_name}: {str(error)}")
        return {}

    @staticmethod
    def validate_required_param(param: Any, param_name: str, func_name: str) -> None:
        """Validate that a required parameter is not None or empty"""
        if param is None:
            raise ValueError(f"{param_name} is required in {func_name}")
        if isinstance(param, (str, list, dict)) and len(param) == 0:
            raise ValueError(f"{param_name} cannot be empty in {func_name}")

    @staticmethod
    def safe_get(dictionary: dict, key: str, default: Any = "") -> Any:
        """Safely get value from dictionary with default"""
        try:
            return dictionary.get(key, default)
        except (AttributeError, TypeError):
            logger.warning(f"Could not access key '{key}' from non-dict object")
            return default

    @staticmethod
    def safe_int_conversion(value: Any, default: int = 0) -> int:
        """Safely convert value to integer"""
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert '{value}' to int, using default {default}")
            return default

    @staticmethod
    def safe_float_conversion(value: Any, default: float = 0.0) -> float:
        """Safely convert value to float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert '{value}' to float, using default {default}")
            return default