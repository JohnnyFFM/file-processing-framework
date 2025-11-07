"""
DataModel: Unified data representation for all file formats.

Simple wrapper around Python dict/list structures with helper methods.
"""

from typing import Any, Union


class DataModel:
    """
    Unified data model for all file formats.

    Stores data as plain Python objects (dict or list) with associated metadata.
    Provides helper methods for common data access patterns.
    """

    def __init__(self, data: Union[dict, list], metadata: dict = None):
        """
        Initialize DataModel.

        Args:
            data: The actual data (dict or list)
            metadata: Optional metadata about the data (source file, formats, etc.)
        """
        self.data = data
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        """
        Convert data to dict format.

        Returns:
            dict: Data as dictionary

        Raises:
            TypeError: If data cannot be converted to dict
        """
        if isinstance(self.data, dict):
            return self.data
        elif isinstance(self.data, list):
            # Convert list to dict with index keys
            return {f"item_{i}": item for i, item in enumerate(self.data)}
        else:
            raise TypeError(f"Cannot convert {type(self.data)} to dict")

    def to_list(self) -> list:
        """
        Convert data to list format.

        Returns:
            list: Data as list

        Raises:
            TypeError: If data cannot be converted to list
        """
        if isinstance(self.data, list):
            return self.data
        elif isinstance(self.data, dict):
            # Convert dict to list of values
            return list(self.data.values())
        else:
            raise TypeError(f"Cannot convert {type(self.data)} to list")

    def get_rows(self) -> list[dict]:
        """
        Get data as list of dictionaries (tabular format).

        Useful for CSV-like data where each row is a dict.

        Returns:
            list[dict]: List of row dictionaries

        Raises:
            TypeError: If data is not in tabular format
        """
        if isinstance(self.data, list):
            if not self.data:
                return []
            if isinstance(self.data[0], dict):
                return self.data
            else:
                raise TypeError("Data is list but items are not dicts")
        else:
            raise TypeError(f"Cannot get rows from {type(self.data)}")

    def get_value(self, path: str, default: Any = None) -> Any:
        """
        Get value from nested data structure using dot notation.

        Examples:
            data = {"user": {"name": "John", "address": {"city": "NYC"}}}
            model.get_value("user.name") → "John"
            model.get_value("user.address.city") → "NYC"
            model.get_value("user.age", 0) → 0 (default)

        Args:
            path: Dot-separated path (e.g., "user.address.city")
            default: Default value if path not found

        Returns:
            Value at path or default
        """
        keys = path.split(".")
        value = self.data

        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value[key]
                elif isinstance(value, list):
                    # Try to convert key to int for list index
                    value = value[int(key)]
                else:
                    return default
            return value
        except (KeyError, IndexError, ValueError, TypeError):
            return default

    def __repr__(self) -> str:
        """String representation of DataModel."""
        data_type = type(self.data).__name__
        data_size = len(self.data) if hasattr(self.data, '__len__') else 'N/A'
        source = self.metadata.get('source_file', 'Unknown')
        return f"DataModel(type={data_type}, size={data_size}, source={source})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.__repr__()
