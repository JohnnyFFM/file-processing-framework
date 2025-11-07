"""
Abstract FileLoader base class.

All file loaders must inherit from this class and implement the load method.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from .data_model import DataModel
from .exceptions import FileLoadError


class FileLoader(ABC):
    """
    Abstract base class for all file loaders.

    Loaders read files and convert them to DataModel instances.

    Extension Point:
        To support a new file format, inherit from this class and implement load().

    Example:
        >>> class NewFormatLoader(FileLoader):
        ...     def load(self, filepath, config):
        ...         # Read file
        ...         with open(filepath, 'r') as f:
        ...             content = f.read()
        ...
        ...         # Parse content
        ...         data = parse_content(content, config)
        ...
        ...         # Create metadata
        ...         metadata = {
        ...             'source_file': filepath,
        ...             'source_file_stem': Path(filepath).stem,
        ...             'source_format': 'newformat'
        ...         }
        ...
        ...         return DataModel(data, metadata)
    """

    @abstractmethod
    def load(self, filepath: str, config: dict) -> DataModel:
        """
        Load file and return DataModel.

        Args:
            filepath: Path to file to load
            config: Configuration dict with parsing options
                   May include: encoding, separators, date formats, etc.

        Returns:
            DataModel: Loaded data with metadata

        Raises:
            FileLoadError: If file cannot be loaded or parsed
            FileNotFoundError: If file does not exist
        """
        pass

    def _validate_file_exists(self, filepath: str) -> None:
        """
        Validate that file exists.

        Args:
            filepath: Path to validate

        Raises:
            FileNotFoundError: If file does not exist
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"File not found: {filepath}")

    def _get_file_metadata(self, filepath: str, format_name: str) -> dict:
        """
        Generate standard metadata for a file.

        Args:
            filepath: Source file path
            format_name: Format name (csv, xml, json)

        Returns:
            dict: Standard metadata dict
        """
        path = Path(filepath)
        return {
            'source_file': str(path.absolute()),
            'source_file_stem': path.stem,
            'source_format': format_name,
        }

    def get_supported_extensions(self) -> list[str]:
        """
        Get list of supported file extensions.

        Override this to specify supported extensions.

        Returns:
            list[str]: List of extensions (e.g., ['.csv', '.tsv'])
        """
        return []
