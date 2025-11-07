"""
Abstract FileWriter base class.

All file writers must inherit from this class and implement the write method.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from .data_model import DataModel
from .exceptions import FileWriteError


class FileWriter(ABC):
    """
    Abstract base class for all file writers.

    Writers convert DataModel instances to files in specific formats.

    Extension Point:
        To support writing a new file format, inherit from this class and implement write().

    Example:
        >>> class NewFormatWriter(FileWriter):
        ...     def write(self, data_model, filepath, config):
        ...         # Extract data
        ...         data = data_model.data
        ...
        ...         # Format according to config
        ...         formatted = format_data(data, config)
        ...
        ...         # Write to file
        ...         with open(filepath, 'w') as f:
        ...             f.write(formatted)
    """

    @abstractmethod
    def write(self, data_model: DataModel, filepath: str, config: dict) -> None:
        """
        Write DataModel to file.

        Args:
            data_model: Data to write
            filepath: Output file path
            config: Configuration dict with formatting options
                   May include: encoding, separators, date formats, etc.

        Raises:
            FileWriteError: If file cannot be written
        """
        pass

    def _ensure_output_directory(self, filepath: str) -> None:
        """
        Ensure output directory exists.

        Args:
            filepath: Output file path

        Raises:
            FileWriteError: If directory cannot be created
        """
        try:
            output_dir = Path(filepath).parent
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileWriteError(f"Cannot create output directory: {e}")

    def _validate_data_model(self, data_model: DataModel) -> None:
        """
        Validate that DataModel has required structure.

        Args:
            data_model: DataModel to validate

        Raises:
            FileWriteError: If DataModel is invalid
        """
        if not isinstance(data_model, DataModel):
            raise FileWriteError(f"Expected DataModel, got {type(data_model)}")

        if data_model.data is None:
            raise FileWriteError("DataModel has no data")

    def get_supported_extensions(self) -> list[str]:
        """
        Get list of supported file extensions.

        Override this to specify supported extensions.

        Returns:
            list[str]: List of extensions (e.g., ['.csv', '.tsv'])
        """
        return []
