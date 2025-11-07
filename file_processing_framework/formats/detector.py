"""
Format detection utilities.

Auto-detect separators, encodings, number formats, and date formats.
"""

import csv
from typing import List, Tuple
import chardet
from .number_parser import NumberParser
from .date_parser import DateParser


class FormatDetector:
    """
    Detect file formats automatically.

    Detects:
    - File encoding
    - CSV separator
    - Number format (decimal/thousands separators)
    - Date format
    """

    def __init__(self):
        """Initialize format detector."""
        self.number_parser = NumberParser()
        self.date_parser = DateParser()

    def detect_encoding(self, filepath: str, sample_size: int = 10000) -> dict:
        """
        Detect file encoding.

        Args:
            filepath: Path to file
            sample_size: Number of bytes to sample

        Returns:
            dict: {'encoding': str, 'confidence': float}

        Examples:
            >>> detector = FormatDetector()
            >>> detector.detect_encoding("data.csv")
            {'encoding': 'utf-8', 'confidence': 0.99}
        """
        try:
            with open(filepath, 'rb') as f:
                sample = f.read(sample_size)

            result = chardet.detect(sample)
            return {
                'encoding': result['encoding'] or 'utf-8',
                'confidence': result['confidence'] or 0.5
            }
        except Exception:
            # Default to UTF-8
            return {'encoding': 'utf-8', 'confidence': 0.5}

    def detect_csv_separator(
        self,
        filepath: str,
        encoding: str = 'utf-8',
        sample_lines: int = 10
    ) -> dict:
        """
        Detect CSV separator (delimiter).

        Args:
            filepath: Path to CSV file
            encoding: File encoding
            sample_lines: Number of lines to sample

        Returns:
            dict: {'separator': str, 'confidence': float}

        Examples:
            >>> detector = FormatDetector()
            >>> detector.detect_csv_separator("data.csv")
            {'separator': ',', 'confidence': 0.95}
        """
        try:
            with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                sample_text = ""
                for i, line in enumerate(f):
                    if i >= sample_lines:
                        break
                    sample_text += line

            # Use csv.Sniffer to detect delimiter
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample_text, delimiters=',;\t|')
                separator = dialect.delimiter

                # Calculate confidence based on consistency
                lines = sample_text.strip().split('\n')
                if len(lines) > 1:
                    counts = [line.count(separator) for line in lines]
                    # Check if all lines have same number of separators
                    if len(set(counts)) == 1:
                        confidence = 0.95
                    else:
                        confidence = 0.7
                else:
                    confidence = 0.6

                return {'separator': separator, 'confidence': confidence}

            except csv.Error:
                # Fallback: count occurrences
                separators = {',': 0, ';': 0, '\t': 0, '|': 0}

                for line in sample_text.split('\n'):
                    for sep in separators:
                        separators[sep] += line.count(sep)

                # Find most common
                best_sep = max(separators.items(), key=lambda x: x[1])

                if best_sep[1] > 0:
                    confidence = 0.6
                    return {'separator': best_sep[0], 'confidence': confidence}
                else:
                    # Default to comma
                    return {'separator': ',', 'confidence': 0.3}

        except Exception:
            # Default to comma
            return {'separator': ',', 'confidence': 0.3}

    def detect_number_format(self, sample_values: List[str]) -> dict:
        """
        Detect number format from sample values.

        Args:
            sample_values: List of string values

        Returns:
            dict: {'decimal_separator': str, 'thousands_separator': str, 'confidence': float}

        Examples:
            >>> detector = FormatDetector()
            >>> detector.detect_number_format(["1,234.56", "2,345.67"])
            {'decimal_separator': '.', 'thousands_separator': ',', 'confidence': 1.0}
        """
        return self.number_parser.detect_format(sample_values)

    def detect_date_format(self, sample_values: List[str]) -> dict:
        """
        Detect date format from sample values.

        Args:
            sample_values: List of string values

        Returns:
            dict: {'format': str, 'confidence': float}

        Examples:
            >>> detector = FormatDetector()
            >>> detector.detect_date_format(["2023-12-31", "2024-01-01"])
            {'format': '%Y-%m-%d', 'confidence': 1.0}
        """
        return self.date_parser.detect_format(sample_values)

    def detect_csv_has_header(
        self,
        filepath: str,
        separator: str = ',',
        encoding: str = 'utf-8'
    ) -> dict:
        """
        Detect if CSV file has a header row.

        Args:
            filepath: Path to CSV file
            separator: CSV separator
            encoding: File encoding

        Returns:
            dict: {'has_header': bool, 'confidence': float}

        Examples:
            >>> detector = FormatDetector()
            >>> detector.detect_csv_has_header("data.csv")
            {'has_header': True, 'confidence': 0.9}
        """
        try:
            with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                sample = ""
                for i, line in enumerate(f):
                    if i >= 20:  # Sample first 20 lines
                        break
                    sample += line

            # Use csv.Sniffer
            sniffer = csv.Sniffer()
            try:
                has_header = sniffer.has_header(sample)
                confidence = 0.8 if has_header else 0.6
                return {'has_header': has_header, 'confidence': confidence}
            except csv.Error:
                # Fallback: check if first row is all strings
                lines = sample.strip().split('\n')
                if len(lines) < 2:
                    return {'has_header': True, 'confidence': 0.5}

                first_row = lines[0].split(separator)
                second_row = lines[1].split(separator)

                # If first row is all non-numeric and second row has numbers, likely header
                first_numeric = sum(1 for val in first_row if self._is_numeric(val))
                second_numeric = sum(1 for val in second_row if self._is_numeric(val))

                if first_numeric == 0 and second_numeric > 0:
                    return {'has_header': True, 'confidence': 0.7}
                else:
                    return {'has_header': True, 'confidence': 0.5}  # Default to True

        except Exception:
            # Default to True (most CSVs have headers)
            return {'has_header': True, 'confidence': 0.5}

    def _is_numeric(self, value: str) -> bool:
        """Check if string value is numeric."""
        if not value:
            return False

        value = value.strip()

        # Remove common separators
        value = value.replace(',', '').replace(' ', '')

        try:
            float(value)
            return True
        except ValueError:
            return False

    def detect_all_csv(self, filepath: str) -> dict:
        """
        Detect all CSV format parameters.

        Args:
            filepath: Path to CSV file

        Returns:
            dict: All detected parameters with confidence scores

        Examples:
            >>> detector = FormatDetector()
            >>> detector.detect_all_csv("data.csv")
            {
                'encoding': 'utf-8',
                'separator': ',',
                'has_header': True,
                'decimal_separator': '.',
                'thousands_separator': ',',
                'confidence': {...}
            }
        """
        # Detect encoding first
        encoding_info = self.detect_encoding(filepath)
        encoding = encoding_info['encoding']

        # Detect separator
        sep_info = self.detect_csv_separator(filepath, encoding)
        separator = sep_info['separator']

        # Detect header
        header_info = self.detect_csv_has_header(filepath, separator, encoding)

        # Read sample values for number/date detection
        sample_values = self._read_csv_sample(filepath, separator, encoding, max_rows=50)

        # Detect number format
        number_format = self.detect_number_format(sample_values)

        # Detect date format
        date_format = self.detect_date_format(sample_values)

        return {
            'encoding': encoding,
            'separator': separator,
            'has_header': header_info['has_header'],
            'decimal_separator': number_format['decimal_separator'],
            'thousands_separator': number_format['thousands_separator'],
            'date_format': date_format['format'],
            'confidence': {
                'encoding': encoding_info['confidence'],
                'separator': sep_info['confidence'],
                'has_header': header_info['confidence'],
                'number_format': number_format['confidence'],
                'date_format': date_format['confidence']
            }
        }

    def _read_csv_sample(
        self,
        filepath: str,
        separator: str,
        encoding: str,
        max_rows: int = 50
    ) -> List[str]:
        """Read sample values from CSV file."""
        sample_values = []

        try:
            with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                reader = csv.reader(f, delimiter=separator)
                for i, row in enumerate(reader):
                    if i >= max_rows:
                        break
                    sample_values.extend(row)

        except Exception:
            pass

        return sample_values
