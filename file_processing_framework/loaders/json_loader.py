"""
JSON file loader.

Loads JSON files and converts them to DataModel.
"""

import json
from pathlib import Path
from typing import Union, Dict, List
from ..core.loader import FileLoader
from ..core.data_model import DataModel
from ..core.exceptions import FileLoadError
from ..formats.detector import FormatDetector


class JsonLoader(FileLoader):
    """
    Load JSON files into DataModel.

    Supports:
    - Auto-detection of encoding
    - Nested structures (dicts and lists)
    - Arrays of objects
    - Single objects
    """

    def __init__(self):
        """Initialize JSON loader."""
        self.detector = FormatDetector()

    def load(self, filepath: str, config: dict) -> DataModel:
        """
        Load JSON file and return DataModel.

        Args:
            filepath: Path to JSON file
            config: Configuration dict with options:
                   - encoding: File encoding (auto-detect if not provided)
                   - root_path: Optional path to extract specific part (e.g., "data.items")

        Returns:
            DataModel: Loaded data as dict or list

        Raises:
            FileLoadError: If file cannot be loaded or parsed
        """
        self._validate_file_exists(filepath)

        try:
            # Get or detect encoding
            encoding = config.get('encoding')
            if not encoding:
                encoding_info = self.detector.detect_encoding(filepath)
                encoding = encoding_info['encoding']

            # Read and parse JSON
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                data = json.load(f)

            # Extract specific path if specified
            root_path = config.get('root_path')
            if root_path:
                data = self._extract_path(data, root_path)

            # Create metadata
            metadata = self._get_file_metadata(filepath, 'json')
            metadata.update({
                'encoding': encoding,
                'data_type': type(data).__name__,
                'size': len(data) if hasattr(data, '__len__') else 1
            })

            # If data is list of dicts, add column info
            if isinstance(data, list) and data and isinstance(data[0], dict):
                metadata['columns'] = list(data[0].keys())
                metadata['row_count'] = len(data)

            return DataModel(data, metadata)

        except json.JSONDecodeError as e:
            raise FileLoadError(f"Invalid JSON in file {filepath}: {e}")
        except Exception as e:
            raise FileLoadError(f"Failed to load JSON file {filepath}: {e}")

    def _extract_path(self, data: Union[dict, list], path: str) -> Union[dict, list]:
        """
        Extract data from nested structure using dot notation.

        Args:
            data: JSON data
            path: Dot-separated path (e.g., "data.items")

        Returns:
            Extracted data

        Raises:
            FileLoadError: If path not found
        """
        keys = path.split('.')
        current = data

        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list):
                    current = current[int(key)]
                else:
                    raise FileLoadError(f"Cannot navigate path '{path}' in JSON data")

            return current

        except (KeyError, IndexError, ValueError) as e:
            raise FileLoadError(f"Path '{path}' not found in JSON data: {e}")

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions."""
        return ['.json']
