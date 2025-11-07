"""
CSV file writer.

Writes DataModel to CSV files.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from ..core.writer import FileWriter
from ..core.data_model import DataModel
from ..core.exceptions import FileWriteError
from ..formats.number_parser import NumberParser
from ..formats.date_parser import DateParser


class CsvWriter(FileWriter):
    """
    Write DataModel to CSV files.

    Supports:
    - Configurable separator, encoding
    - Number formatting (decimal/thousands separators)
    - Date formatting
    - Optional headers
    """

    def __init__(self):
        """Initialize CSV writer."""
        self.number_parser = None
        self.date_parser = None

    def write(self, data_model: DataModel, filepath: str, config: dict) -> None:
        """
        Write DataModel to CSV file.

        Args:
            data_model: Data to write
            filepath: Output file path
            config: Configuration dict with options:
                   - encoding: File encoding (default: utf-8)
                   - separator: CSV delimiter (default: ,)
                   - has_header: Write header row (default: True)
                   - decimal_separator: Number decimal separator
                   - thousands_separator: Number thousands separator
                   - date_format: Date format string

        Raises:
            FileWriteError: If file cannot be written
        """
        self._validate_data_model(data_model)
        self._ensure_output_directory(filepath)

        try:
            # Get configuration
            encoding = config.get('encoding', 'utf-8')
            separator = config.get('separator', ',')
            has_header = config.get('has_header', True)
            decimal_sep = config.get('decimal_separator', '.')
            thousands_sep = config.get('thousands_separator', ',')
            date_format = config.get('date_format', '%Y-%m-%d')

            # Initialize formatters
            self.number_parser = NumberParser(decimal_sep, thousands_sep)
            self.date_parser = DateParser()

            # Convert data to list of dicts
            rows = self._prepare_data(data_model)

            if not rows:
                raise FileWriteError("No data to write")

            # Get column names
            columns = list(rows[0].keys())

            # Write CSV
            with open(filepath, 'w', encoding=encoding, newline='', errors='replace') as f:
                writer = csv.DictWriter(f, fieldnames=columns, delimiter=separator)

                if has_header:
                    writer.writeheader()

                for row in rows:
                    # Format values
                    formatted_row = self._format_row(row, date_format)
                    writer.writerow(formatted_row)

        except Exception as e:
            raise FileWriteError(f"Failed to write CSV file {filepath}: {e}")

    def _prepare_data(self, data_model: DataModel) -> List[Dict[str, Any]]:
        """
        Convert DataModel to list of dicts.

        Args:
            data_model: DataModel instance

        Returns:
            List of row dicts

        Raises:
            FileWriteError: If data format is not suitable for CSV
        """
        data = data_model.data

        # If already list of dicts, use as-is
        if isinstance(data, list):
            if not data:
                return []
            if isinstance(data[0], dict):
                return data
            else:
                # List of primitives, convert to single-column dicts
                return [{'value': item} for item in data]

        # If dict, try to convert
        elif isinstance(data, dict):
            # Check if dict values are lists of same length (column-oriented data)
            if all(isinstance(v, list) for v in data.values()):
                lengths = [len(v) for v in data.values()]
                if len(set(lengths)) == 1:
                    # Convert column-oriented to row-oriented
                    columns = list(data.keys())
                    rows = []
                    for i in range(lengths[0]):
                        row = {col: data[col][i] for col in columns}
                        rows.append(row)
                    return rows

            # Single row dict
            return [data]

        else:
            raise FileWriteError(f"Cannot convert {type(data)} to CSV format")

    def _format_row(self, row: Dict[str, Any], date_format: str) -> Dict[str, str]:
        """
        Format row values to strings.

        Args:
            row: Row dict with values
            date_format: Date format string

        Returns:
            Row dict with formatted string values
        """
        formatted = {}

        for key, value in row.items():
            if value is None:
                formatted[key] = ''
            elif isinstance(value, datetime):
                formatted[key] = self.date_parser.format(value, date_format)
            elif isinstance(value, (int, float)):
                formatted[key] = self.number_parser.format(value)
            elif isinstance(value, bool):
                formatted[key] = str(value)
            elif isinstance(value, (dict, list)):
                # Convert complex types to string representation
                formatted[key] = str(value)
            else:
                formatted[key] = str(value)

        return formatted

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions."""
        return ['.csv', '.tsv', '.txt']
