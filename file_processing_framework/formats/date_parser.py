"""
Date format parser.

Handles different date formats using python-dateutil and custom patterns.
"""

from datetime import datetime
from typing import Union, List
from dateutil import parser as dateutil_parser


class DateParser:
    """
    Parse dates in various formats.

    Handles:
    - ISO 8601 (2023-12-31)
    - European (31.12.2023, 31/12/2023)
    - US (12/31/2023)
    - Custom formats (specified in config)
    - Timestamps (Unix epoch)
    """

    # Common date format patterns
    COMMON_FORMATS = [
        "%Y-%m-%d",           # ISO: 2023-12-31
        "%d.%m.%Y",           # European: 31.12.2023
        "%d/%m/%Y",           # European: 31/12/2023
        "%m/%d/%Y",           # US: 12/31/2023
        "%Y/%m/%d",           # Asian: 2023/12/31
        "%d-%m-%Y",           # European: 31-12-2023
        "%Y-%m-%d %H:%M:%S",  # ISO with time
        "%d.%m.%Y %H:%M:%S",  # European with time
        "%m/%d/%Y %H:%M:%S",  # US with time
    ]

    def __init__(self, date_formats: List[str] = None):
        """
        Initialize date parser.

        Args:
            date_formats: List of date format strings (strptime format)
                         If None, will use common formats + fuzzy parsing
        """
        self.date_formats = date_formats or self.COMMON_FORMATS

    def parse(self, value: str, fuzzy: bool = True) -> Union[datetime, str]:
        """
        Parse a string value to datetime if possible.

        Args:
            value: String value to parse
            fuzzy: If True, use fuzzy parsing as fallback

        Returns:
            datetime object or original string if not a date

        Examples:
            >>> parser = DateParser()
            >>> parser.parse("2023-12-31")
            datetime.datetime(2023, 12, 31, 0, 0)
            >>> parser.parse("31.12.2023")
            datetime.datetime(2023, 12, 31, 0, 0)
            >>> parser.parse("not a date")
            "not a date"
        """
        if not isinstance(value, str):
            return value

        value = value.strip()

        if not value:
            return value

        # Try specific formats first
        for fmt in self.date_formats:
            try:
                return datetime.strptime(value, fmt)
            except (ValueError, TypeError):
                continue

        # Try dateutil fuzzy parsing
        if fuzzy:
            try:
                return dateutil_parser.parse(value, fuzzy=True)
            except (ValueError, TypeError, dateutil_parser.ParserError):
                pass

        # Try Unix timestamp
        try:
            timestamp = float(value)
            # Reasonable range for timestamps (1970-2100)
            if 0 < timestamp < 4102444800:
                return datetime.fromtimestamp(timestamp)
        except (ValueError, OSError):
            pass

        # Not a date, return original
        return value

    def format(self, value: datetime, format_string: str = "%Y-%m-%d") -> str:
        """
        Format a datetime to string.

        Args:
            value: datetime to format
            format_string: Output format (strftime format)

        Returns:
            str: Formatted date string

        Examples:
            >>> parser = DateParser()
            >>> dt = datetime(2023, 12, 31)
            >>> parser.format(dt, "%d.%m.%Y")
            "31.12.2023"
        """
        if not isinstance(value, datetime):
            return str(value)

        return value.strftime(format_string)

    def detect_format(self, sample_values: List[str]) -> dict:
        """
        Detect date format from sample values.

        Args:
            sample_values: List of string values to analyze

        Returns:
            dict: Detected format with confidence
                 {'format': str, 'confidence': float}

        Examples:
            >>> parser = DateParser()
            >>> parser.detect_format(["31.12.2023", "01.01.2024", "15.06.2024"])
            {'format': '%d.%m.%Y', 'confidence': 1.0}
        """
        format_counts = {fmt: 0 for fmt in self.COMMON_FORMATS}
        total_dates = 0

        for value in sample_values:
            if not isinstance(value, str):
                continue

            value = value.strip()

            # Try each format
            for fmt in self.COMMON_FORMATS:
                try:
                    datetime.strptime(value, fmt)
                    format_counts[fmt] += 1
                    total_dates += 1
                    break  # Found a match, stop trying other formats
                except (ValueError, TypeError):
                    continue

        # Find most common format
        if total_dates == 0:
            return {'format': '%Y-%m-%d', 'confidence': 0.0}

        best_format = max(format_counts.items(), key=lambda x: x[1])
        confidence = best_format[1] / len(sample_values) if sample_values else 0.0

        return {
            'format': best_format[0],
            'confidence': min(confidence, 1.0)
        }

    def is_date(self, value: str) -> bool:
        """
        Check if a string value looks like a date.

        Args:
            value: String to check

        Returns:
            bool: True if value can be parsed as date
        """
        result = self.parse(value, fuzzy=True)
        return isinstance(result, datetime)
