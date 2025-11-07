"""
Abstract Task base class.

All processing tasks must inherit from this class and implement the execute method.
"""

from abc import ABC, abstractmethod
from typing import Tuple
from .data_model import DataModel


class Task(ABC):
    """
    Abstract base class for all processing tasks.

    Tasks transform input data and return processed data along with an output filename.

    Extension Point:
        To create a new task, inherit from this class and implement execute().

    Example:
        >>> class MyTask(Task):
        ...     def execute(self, data_model, params, input_filename):
        ...         # Process data
        ...         processed_data = DataModel(...)
        ...
        ...         # Generate output name
        ...         output_name = f"{Path(input_filename).stem}_processed"
        ...
        ...         return processed_data, output_name
    """

    @abstractmethod
    def execute(
        self,
        data_model: DataModel,
        params: dict,
        input_filename: str
    ) -> Tuple[DataModel, str]:
        """
        Execute the task on input data.

        Args:
            data_model: Input data to process
            params: Task parameters from configuration or defaults
            input_filename: Original input filename (e.g., "sales_data.csv")
                          Use this to generate meaningful output names

        Returns:
            Tuple of:
                - DataModel: Processed data (can be modified original or new instance)
                - str: Output filename WITHOUT extension (e.g., "sales_data_processed")
                      The framework will add the appropriate extension based on output format

        Raises:
            TaskError: If task execution fails

        Example:
            >>> def execute(self, data_model, params, input_filename):
            ...     # Extract filename without extension
            ...     from pathlib import Path
            ...     file_stem = Path(input_filename).stem
            ...
            ...     # Process data (example: add a field)
            ...     if isinstance(data_model.data, list):
            ...         for row in data_model.data:
            ...             row['processed'] = True
            ...
            ...     # Generate output name
            ...     output_name = f"{file_stem}_task_output"
            ...
            ...     return data_model, output_name
        """
        pass

    def validate_params(self, params: dict) -> bool:
        """
        Optional: Validate task parameters.

        Override this method to add parameter validation.

        Args:
            params: Parameters to validate

        Returns:
            bool: True if valid

        Raises:
            ValueError: If parameters are invalid
        """
        return True

    def get_name(self) -> str:
        """
        Get task name.

        Returns:
            str: Task class name
        """
        return self.__class__.__name__
