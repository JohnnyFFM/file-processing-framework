"""
JSON file writer.

Writes DataModel to JSON files.
"""

import json
from datetime import datetime
from typing import Any, Union, Dict, List
from ..core.writer import FileWriter
from ..core.data_model import DataModel
from ..core.exceptions import FileWriteError


class JsonWriter(FileWriter):
    """
    Write DataModel to JSON files.

    Supports:
    - Configurable indentation
    - Custom encoding
    - Automatic datetime serialization
    """

    def write(self, data_model: DataModel, filepath: str, config: dict) -> None:
        """
        Write DataModel to JSON file.

        Args:
            data_model: Data to write
            filepath: Output file path
            config: Configuration dict with options:
                   - encoding: File encoding (default: utf-8)
                   - indent: Indentation spaces (default: 2, None for compact)
                   - sort_keys: Sort dict keys (default: False)
                   - ensure_ascii: Ensure ASCII output (default: False)

        Raises:
            FileWriteError: If file cannot be written
        """
        self._validate_data_model(data_model)
        self._ensure_output_directory(filepath)

        try:
            # Get configuration
            encoding = config.get('encoding', 'utf-8')
            indent = config.get('indent', 2)
            sort_keys = config.get('sort_keys', False)
            ensure_ascii = config.get('ensure_ascii', False)

            # Prepare data (handle datetime and other non-JSON types)
            data = self._prepare_data(data_model.data)

            # Write JSON
            with open(filepath, 'w', encoding=encoding, errors='replace') as f:
                json.dump(
                    data,
                    f,
                    indent=indent,
                    sort_keys=sort_keys,
                    ensure_ascii=ensure_ascii,
                    default=self._json_serializer
                )

        except Exception as e:
            raise FileWriteError(f"Failed to write JSON file {filepath}: {e}")

    def _prepare_data(self, data: Any) -> Any:
        """
        Prepare data for JSON serialization.

        Recursively convert datetime and other special types.

        Args:
            data: Data to prepare

        Returns:
            JSON-serializable data
        """
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {key: self._prepare_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._prepare_data(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            # Convert other types to string
            return str(data)

    def _json_serializer(self, obj: Any) -> Any:
        """
        Custom JSON serializer for non-standard types.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return str(obj)

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions."""
        return ['.json']
