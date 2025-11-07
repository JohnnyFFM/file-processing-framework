"""
Custom exceptions for the file processing framework.
"""


class FrameworkException(Exception):
    """Base exception for all framework errors."""
    pass


class FileLoadError(FrameworkException):
    """Raised when a file cannot be loaded or parsed."""
    pass


class FileWriteError(FrameworkException):
    """Raised when a file cannot be written."""
    pass


class ConfigError(FrameworkException):
    """Raised when configuration is invalid or cannot be loaded."""
    pass


class TaskError(FrameworkException):
    """Raised when a task execution fails."""
    pass


class FormatDetectionError(FrameworkException):
    """Raised when format auto-detection fails."""
    pass


class UnsupportedFormatError(FrameworkException):
    """Raised when an unsupported file format is encountered."""
    pass


class ValidationError(FrameworkException):
    """Raised when data validation fails."""
    pass
