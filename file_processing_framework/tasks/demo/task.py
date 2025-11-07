"""
Demo Task - Example implementation.

This task demonstrates how to create custom tasks.
It passes data through with minimal modification.
"""

from pathlib import Path
from ...core.task import Task
from ...core.data_model import DataModel


class DemoTask(Task):
    """
    Demo task that passes data through with minimal changes.

    This task demonstrates:
    - How to access input data
    - How to work with parameters
    - How to generate output filenames
    - How to return processed data

    The task adds a 'processed' flag to demonstrate data modification.
    """

    def execute(
        self,
        data_model: DataModel,
        params: dict,
        input_filename: str
    ) -> tuple[DataModel, str]:
        """
        Execute demo task.

        Args:
            data_model: Input data
            params: Task parameters (can include custom settings)
            input_filename: Original input filename

        Returns:
            Tuple of (processed_data_model, output_filename)
        """
        # Extract filename stem (without extension)
        file_stem = Path(input_filename).stem

        # Access parameters (with defaults)
        add_processed_flag = params.get('add_processed_flag', True)
        output_suffix = params.get('output_suffix', 'demo')

        # Process data
        processed_data = self._process_data(data_model, add_processed_flag)

        # Generate output filename
        output_name = f"{file_stem}_{output_suffix}"

        return processed_data, output_name

    def _process_data(self, data_model: DataModel, add_flag: bool) -> DataModel:
        """
        Process the data.

        This demo adds a 'processed' field to show data modification.

        Args:
            data_model: Input data model
            add_flag: Whether to add processed flag

        Returns:
            DataModel: Processed data
        """
        data = data_model.data

        if not add_flag:
            # Pass through unchanged
            return data_model

        # Process based on data type
        if isinstance(data, list):
            # List of dicts (CSV-like data)
            if data and isinstance(data[0], dict):
                processed_list = []
                for item in data:
                    new_item = item.copy()
                    new_item['processed'] = True
                    new_item['task_name'] = 'DemoTask'
                    processed_list.append(new_item)
                data = processed_list
            # List of primitives - wrap in dict
            else:
                data = [
                    {
                        'original_value': item,
                        'processed': True,
                        'task_name': 'DemoTask'
                    }
                    for item in data
                ]

        elif isinstance(data, dict):
            # Add processing metadata to dict
            data = data.copy()
            data['_metadata'] = {
                'processed': True,
                'task_name': 'DemoTask'
            }

        else:
            # Wrap primitive in dict
            data = {
                'original_value': data,
                'processed': True,
                'task_name': 'DemoTask'
            }

        # Create new DataModel with processed data
        new_metadata = data_model.metadata.copy()
        new_metadata['task_applied'] = 'DemoTask'
        new_metadata['task_parameters'] = {'add_processed_flag': add_flag}

        return DataModel(data, new_metadata)

    def validate_params(self, params: dict) -> bool:
        """
        Validate task parameters.

        Args:
            params: Parameters to validate

        Returns:
            bool: True if valid

        Raises:
            ValueError: If parameters are invalid
        """
        # Check if add_processed_flag is boolean (if provided)
        if 'add_processed_flag' in params:
            if not isinstance(params['add_processed_flag'], bool):
                raise ValueError("Parameter 'add_processed_flag' must be boolean")

        # Check if output_suffix is string (if provided)
        if 'output_suffix' in params:
            if not isinstance(params['output_suffix'], str):
                raise ValueError("Parameter 'output_suffix' must be string")

        return True
