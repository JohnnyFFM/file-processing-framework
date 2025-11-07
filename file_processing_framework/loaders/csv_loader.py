"""
CSV file loader.

Loads CSV files and converts them to DataModel.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from ..core.loader import FileLoader
from ..core.data_model import DataModel
from ..core.exceptions import FileLoadError
from ..formats.detector import FormatDetector
from ..formats.number_parser import NumberParser
from ..formats.date_parser import DateParser


class CsvLoader(FileLoader):
    """
    Load CSV files into DataModel.

    Supports:
    - Auto-detection of separator, encoding, headers
    - Manual configuration via config dict
    - Different number and date formats
    - Files with or without headers
    """

    def __init__(self):
        """Initialize CSV loader."""
        self.detector = FormatDetector()
        self.number_parser = None
        self.date_parser = None

    def load(self, filepath: str, config: dict) -> DataModel:
        """
        Load CSV file and return DataModel.

        Args:
            filepath: Path to CSV file
            config: Configuration dict with options:
                   - encoding: File encoding (auto-detect if not provided)
                   - separator: CSV delimiter (auto-detect if not provided)
                   - has_header: Whether file has header row (auto-detect if not provided)
                   - columns: Column names if no header
                   - decimal_separator: Number decimal separator
                   - thousands_separator: Number thousands separator
                   - date_formats: List of date format strings

        Returns:
            DataModel: Loaded data as list of dicts

        Raises:
            FileLoadError: If file cannot be loaded
        """
        self._validate_file_exists(filepath)

        try:
            # Get or detect encoding
            encoding = config.get('encoding')
            if not encoding:
                encoding_info = self.detector.detect_encoding(filepath)
                encoding = encoding_info['encoding']

            # Get or detect separator
            separator = config.get('separator')
            if not separator:
                sep_info = self.detector.detect_csv_separator(filepath, encoding)
                separator = sep_info['separator']

            # Get or detect has_header
            has_header = config.get('has_header')
            if has_header is None:
                header_info = self.detector.detect_csv_has_header(filepath, separator, encoding)
                has_header = header_info['has_header']

            # Initialize parsers
            decimal_sep = config.get('decimal_separator', '.')
            thousands_sep = config.get('thousands_separator', ',')
            self.number_parser = NumberParser(decimal_sep, thousands_sep)

            date_formats = config.get('date_formats')
            self.date_parser = DateParser(date_formats)

            # Read CSV
            data = self._read_csv(
                filepath,
                encoding,
                separator,
                has_header,
                config.get('columns')
            )

            # Parse values (numbers and dates)
            if config.get('parse_values', True):
                data = self._parse_values(data)

            # Create metadata
            metadata = self._get_file_metadata(filepath, 'csv')
            metadata.update({
                'encoding': encoding,
                'separator': separator,
                'has_header': has_header,
                'decimal_separator': decimal_sep,
                'thousands_separator': thousands_sep,
                'row_count': len(data),
                'columns': list(data[0].keys()) if data else []
            })

            return DataModel(data, metadata)

        except Exception as e:
            raise FileLoadError(f"Failed to load CSV file {filepath}: {e}")

    def _read_csv(
        self,
        filepath: str,
        encoding: str,
        separator: str,
        has_header: bool,
        column_names: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Read CSV file into list of dicts.

        Args:
            filepath: Path to file
            encoding: File encoding
            separator: CSV delimiter
            has_header: Whether file has header
            column_names: Column names if no header

        Returns:
            List of dicts, one per row
        """
        data = []

        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            reader = csv.reader(f, delimiter=separator)

            # Get or generate column names
            if has_header:
                try:
                    columns = next(reader)
                except StopIteration:
                    raise FileLoadError("CSV file is empty")
            else:
                if column_names:
                    columns = column_names
                else:
                    # Read first row to determine number of columns
                    try:
                        first_row = next(reader)
                        columns = [f"col_{i}" for i in range(len(first_row))]
                        # Put first row back by processing it
                        row_dict = dict(zip(columns, first_row))
                        data.append(row_dict)
                    except StopIteration:
                        raise FileLoadError("CSV file is empty")

            # Read data rows
            for row in reader:
                # Skip empty rows
                if not row or all(not cell.strip() for cell in row):
                    continue

                # Pad row if shorter than columns
                while len(row) < len(columns):
                    row.append('')

                # Truncate if longer
                row = row[:len(columns)]

                # Create dict
                row_dict = dict(zip(columns, row))
                data.append(row_dict)

        return data

    def _parse_values(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse string values to appropriate types (numbers, dates).

        Args:
            data: List of row dicts with string values

        Returns:
            List of row dicts with parsed values
        """
        parsed_data = []

        for row in data:
            parsed_row = {}
            for key, value in row.items():
                if not isinstance(value, str):
                    parsed_row[key] = value
                    continue

                # Try to parse as number
                parsed_value = self.number_parser.parse(value)

                # If still string, try to parse as date
                if isinstance(parsed_value, str):
                    parsed_value = self.date_parser.parse(value, fuzzy=False)

                parsed_row[key] = parsed_value

            parsed_data.append(parsed_row)

        return parsed_data

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions."""
        return ['.csv', '.tsv', '.txt']
