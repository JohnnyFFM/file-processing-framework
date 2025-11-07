"""
Number format parser.

Handles different number formats (decimal separators, thousands separators, scientific notation).
"""

import re
from typing import Union


class NumberParser:
    """
    Parse numbers in various formats.

    Handles:
    - Different decimal separators (. or ,)
    - Different thousands separators (. , space, or none)
    - Scientific notation (1.23e10)
    - Negative numbers
    - Integer vs float detection
    """

    def __init__(self, decimal_separator: str = ".", thousands_separator: str = ","):
        """
        Initialize number parser.

        Args:
            decimal_separator: Decimal separator character (default: ".")
            thousands_separator: Thousands separator character (default: ",")
        """
        self.decimal_separator = decimal_separator
        self.thousands_separator = thousands_separator

    def parse(self, value: str) -> Union[int, float, str]:
        """
        Parse a string value to number if possible.

        Args:
            value: String value to parse

        Returns:
            int, float, or original string if not a number

        Examples:
            >>> parser = NumberParser(decimal_separator=",", thousands_separator=".")
            >>> parser.parse("1.234,56")
            1234.56
            >>> parser.parse("1,234.56")  # with default settings
            1234.56
            >>> parser.parse("1.23e10")
            12300000000.0
        """
        if not isinstance(value, str):
            return value

        # Strip whitespace
        value = value.strip()

        if not value:
            return value

        # Try to detect and parse number
        try:
            # Check for scientific notation
            if 'e' in value.lower():
                return float(value)

            # Remove thousands separator
            if self.thousands_separator:
                value = value.replace(self.thousands_separator, "")

            # Replace decimal separator with standard dot
            if self.decimal_separator != ".":
                value = value.replace(self.decimal_separator, ".")

            # Try to parse
            if "." in value:
                return float(value)
            else:
                return int(value)

        except (ValueError, AttributeError):
            # Not a number, return original
            return value

    def format(self, value: Union[int, float], decimal_places: int = None) -> str:
        """
        Format a number according to configured separators.

        Args:
            value: Number to format
            decimal_places: Optional decimal places (default: auto)

        Returns:
            str: Formatted number string

        Examples:
            >>> parser = NumberParser(decimal_separator=",", thousands_separator=".")
            >>> parser.format(1234.56)
            "1.234,56"
        """
        if not isinstance(value, (int, float)):
            return str(value)

        # Format with decimal places if specified
        if decimal_places is not None:
            value_str = f"{value:.{decimal_places}f}"
        else:
            value_str = str(value)

        # Split integer and decimal parts
        if "." in value_str:
            integer_part, decimal_part = value_str.split(".")
        else:
            integer_part = value_str
            decimal_part = None

        # Add thousands separator
        if self.thousands_separator and len(integer_part) > 3:
            # Handle negative numbers
            if integer_part.startswith("-"):
                sign = "-"
                integer_part = integer_part[1:]
            else:
                sign = ""

            # Add separators from right to left
            parts = []
            for i in range(len(integer_part), 0, -3):
                start = max(0, i - 3)
                parts.insert(0, integer_part[start:i])

            integer_part = sign + self.thousands_separator.join(parts)

        # Combine parts
        if decimal_part:
            return f"{integer_part}{self.decimal_separator}{decimal_part}"
        else:
            return integer_part

    def detect_format(self, sample_values: list[str]) -> dict:
        """
        Detect number format from sample values.

        Args:
            sample_values: List of string values to analyze

        Returns:
            dict: Detected format with confidence
                 {'decimal_separator': str, 'thousands_separator': str, 'confidence': float}

        Examples:
            >>> parser = NumberParser()
            >>> parser.detect_format(["1.234,56", "2.456,78", "3.678,90"])
            {'decimal_separator': ',', 'thousands_separator': '.', 'confidence': 1.0}
        """
        # Count occurrences of potential separators
        dot_as_decimal = 0
        comma_as_decimal = 0
        dot_as_thousands = 0
        comma_as_thousands = 0

        number_pattern = re.compile(r'[0-9.,]+')

        for value in sample_values:
            if not isinstance(value, str):
                continue

            value = value.strip()
            if not number_pattern.match(value):
                continue

            # Check if looks like number
            if value.count('.') == 1 and value.count(',') == 0:
                # Could be decimal or thousands
                parts = value.split('.')
                if len(parts[1]) <= 2:  # Likely decimal
                    dot_as_decimal += 1
                else:
                    dot_as_thousands += 1

            elif value.count(',') == 1 and value.count('.') == 0:
                parts = value.split(',')
                if len(parts[1]) <= 2:
                    comma_as_decimal += 1
                else:
                    comma_as_thousands += 1

            elif '.' in value and ',' in value:
                # Both present, determine which is decimal
                last_dot = value.rfind('.')
                last_comma = value.rfind(',')

                if last_dot > last_comma:
                    dot_as_decimal += 1
                    comma_as_thousands += 1
                else:
                    comma_as_decimal += 1
                    dot_as_thousands += 1

        # Determine most likely format
        total_samples = len([v for v in sample_values if isinstance(v, str)])

        if total_samples == 0:
            return {'decimal_separator': '.', 'thousands_separator': ',', 'confidence': 0.0}

        # Decide based on counts
        if dot_as_decimal > comma_as_decimal:
            decimal_sep = '.'
            thousands_sep = ','
        elif comma_as_decimal > dot_as_decimal:
            decimal_sep = ','
            thousands_sep = '.'
        else:
            # Default
            decimal_sep = '.'
            thousands_sep = ','

        # Calculate confidence
        confidence = max(dot_as_decimal, comma_as_decimal) / total_samples if total_samples > 0 else 0.5

        return {
            'decimal_separator': decimal_sep,
            'thousands_separator': thousands_sep,
            'confidence': min(confidence, 1.0)
        }
