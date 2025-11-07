"""
TaskRunner - Main orchestrator.

Coordinates the entire processing workflow:
Load → Process → Write
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Type, Optional
from .data_model import DataModel
from .task import Task
from .loader import FileLoader
from .writer import FileWriter
from .exceptions import (
    FrameworkException,
    FileLoadError,
    FileWriteError,
    TaskError,
    UnsupportedFormatError,
    ConfigError
)
from ..config.config_loader import ConfigLoader
from ..loaders.csv_loader import CsvLoader
from ..loaders.json_loader import JsonLoader
from ..loaders.xml_loader import XmlLoader
from ..writers.csv_writer import CsvWriter
from ..writers.json_writer import JsonWriter
from ..writers.xml_writer import XmlWriter


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskRunner:
    """
    Main orchestrator for the file processing framework.

    Handles:
    1. Configuration loading and merging
    2. File format detection
    3. Loader selection and execution
    4. Task execution
    5. Writer selection and execution

    Simple monolithic design - no pipeline complexity.
    """

    # Format to loader mapping
    LOADERS: Dict[str, Type[FileLoader]] = {
        '.csv': CsvLoader,
        '.tsv': CsvLoader,
        '.txt': CsvLoader,
        '.json': JsonLoader,
        '.xml': XmlLoader,
    }

    # Format to writer mapping
    WRITERS: Dict[str, Type[FileWriter]] = {
        'csv': CsvWriter,
        'json': JsonWriter,
        'xml': XmlWriter,
    }

    def __init__(self):
        """Initialize TaskRunner."""
        self.config_loader = ConfigLoader()

    def run(
        self,
        input_files: List[str],
        task: Task,
        output_dir: str,
        config_file: Optional[str] = None,
        cli_overrides: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Run the processing workflow.

        Args:
            input_files: List of input file paths (all must be same format)
            task: Task instance to execute
            output_dir: Output directory path
            config_file: Optional configuration file path
            cli_overrides: Optional CLI parameter overrides

        Returns:
            List of output file paths

        Raises:
            FrameworkException: If processing fails
        """
        logger.info(f"Starting TaskRunner with {len(input_files)} input file(s)")

        # Load and merge configuration
        config = self._load_config(config_file, cli_overrides)

        # Validate configuration
        self.config_loader.validate_config(config)

        # Get output format from config
        output_format = config['task']['output']['format']
        logger.info(f"Output format from config: {output_format}")

        # Validate all input files match expected format
        self._validate_input_files(input_files, config)

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Process each file (loop)
        output_files = []
        total_files = len(input_files)

        for index, input_file in enumerate(input_files, start=1):
            try:
                logger.info(f"Processing file {index} of {total_files}: {input_file}")

                # Step 1: Load file
                data_model = self._load_file(input_file, config)
                logger.info(f"Loaded {data_model.metadata.get('row_count', 'N/A')} records")

                # Step 2: Execute task
                processed_data, output_name = self._execute_task(
                    task,
                    data_model,
                    config,
                    input_file
                )
                logger.info(f"Task executed: {task.get_name()}")

                # Step 3: Write output
                output_file = self._write_output(
                    processed_data,
                    output_name,
                    output_format,
                    output_dir,
                    config
                )
                logger.info(f"Output written: {output_file}")

                output_files.append(output_file)

            except FrameworkException as e:
                logger.error(f"Failed to process {input_file}: {e}")
                raise

        logger.info(f"TaskRunner completed successfully. Generated {len(output_files)} output file(s)")
        return output_files

    def _validate_input_files(self, input_files: List[str], config: Dict[str, Any]) -> None:
        """
        Validate that all input files match the expected format from config.

        Args:
            input_files: List of input file paths
            config: Configuration dict

        Raises:
            UnsupportedFormatError: If files don't match expected format
        """
        expected_format = config['task']['input']['format']
        format_to_extensions = {
            'csv': ['.csv', '.tsv', '.txt'],
            'json': ['.json'],
            'xml': ['.xml']
        }

        expected_extensions = format_to_extensions.get(expected_format, [])

        for filepath in input_files:
            extension = Path(filepath).suffix.lower()
            if extension not in expected_extensions:
                raise UnsupportedFormatError(
                    f"File '{filepath}' has extension '{extension}' but task expects '{expected_format}' format. "
                    f"Expected extensions: {', '.join(expected_extensions)}"
                )

        logger.info(f"All {len(input_files)} input files validated as {expected_format} format")

    def _load_config(
        self,
        config_file: Optional[str],
        cli_overrides: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Load and merge configuration.

        Priority: CLI overrides > Config file > Defaults

        Args:
            config_file: Configuration file path (optional)
            cli_overrides: CLI parameter overrides (optional)

        Returns:
            dict: Merged configuration
        """
        # Start with defaults
        config = self.config_loader.get_default_config()

        # Load config file if provided
        if config_file:
            try:
                file_config = self.config_loader.load(config_file)
                config = self.config_loader.merge_configs(config, file_config)
                logger.info(f"Loaded configuration from: {config_file}")
            except Exception as e:
                raise ConfigError(f"Failed to load config file: {e}")

        # Apply CLI overrides
        if cli_overrides:
            config = self.config_loader.merge_configs(config, cli_overrides)
            logger.debug("Applied CLI overrides")

        return config

    def _load_file(self, filepath: str, config: Dict[str, Any]) -> DataModel:
        """
        Load input file using appropriate loader.

        Args:
            filepath: Input file path
            config: Configuration dict

        Returns:
            DataModel: Loaded data

        Raises:
            FileLoadError: If file cannot be loaded
            UnsupportedFormatError: If file format is not supported
        """
        # Detect file format from extension
        extension = Path(filepath).suffix.lower()

        if extension not in self.LOADERS:
            raise UnsupportedFormatError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {', '.join(self.LOADERS.keys())}"
            )

        # Get loader class and instantiate
        loader_class = self.LOADERS[extension]
        loader = loader_class()

        # Extract input configuration for this format
        input_config = self._get_input_config(extension, config)

        # Load file
        try:
            data_model = loader.load(filepath, input_config)
            return data_model
        except Exception as e:
            raise FileLoadError(f"Failed to load file {filepath}: {e}")

    def _execute_task(
        self,
        task: Task,
        data_model: DataModel,
        config: Dict[str, Any],
        input_filename: str
    ) -> tuple[DataModel, str]:
        """
        Execute task on data.

        Args:
            task: Task instance
            data_model: Input data
            config: Configuration dict
            input_filename: Original input filename

        Returns:
            Tuple of (processed_data, output_filename)

        Raises:
            TaskError: If task execution fails
        """
        # Get task parameters from config
        task_params = config.get('task', {}).get('parameters', {})

        # Execute task
        try:
            processed_data, output_name = task.execute(
                data_model,
                task_params,
                input_filename
            )

            if not isinstance(processed_data, DataModel):
                raise TaskError(
                    f"Task must return DataModel, got {type(processed_data)}"
                )

            if not isinstance(output_name, str):
                raise TaskError(
                    f"Task must return output name as string, got {type(output_name)}"
                )

            return processed_data, output_name

        except Exception as e:
            raise TaskError(f"Task execution failed: {e}")

    def _write_output(
        self,
        data_model: DataModel,
        output_name: str,
        output_format: str,
        output_dir: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Write output file using appropriate writer.

        Args:
            data_model: Data to write
            output_name: Output filename (without extension)
            output_format: Output format (csv, json, xml)
            output_dir: Output directory
            config: Configuration dict

        Returns:
            str: Output file path

        Raises:
            FileWriteError: If file cannot be written
            UnsupportedFormatError: If output format is not supported
        """
        # Validate output format
        if output_format not in self.WRITERS:
            raise UnsupportedFormatError(
                f"Unsupported output format: {output_format}. "
                f"Supported formats: {', '.join(self.WRITERS.keys())}"
            )

        # Get writer class and instantiate
        writer_class = self.WRITERS[output_format]
        writer = writer_class()

        # Build output filepath
        output_filepath = str(Path(output_dir) / f"{output_name}.{output_format}")

        # Extract output configuration for this format
        output_config = self._get_output_config(output_format, config)

        # Write file
        try:
            writer.write(data_model, output_filepath, output_config)
            return output_filepath
        except Exception as e:
            raise FileWriteError(f"Failed to write output file: {e}")

    def _get_input_config(self, extension: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract input configuration for specific file format.

        Args:
            extension: File extension (e.g., '.csv')
            config: Full configuration dict

        Returns:
            dict: Input configuration for the format
        """
        # Get input config from task.input.config
        input_config = config.get('task', {}).get('input', {}).get('config', {}).copy()

        return input_config

    def _get_output_config(self, output_format: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract output configuration for specific file format.

        Args:
            output_format: Output format (csv, json, xml)
            config: Full configuration dict

        Returns:
            dict: Output configuration for the format
        """
        # Get output config from task.output.config
        output_config = config.get('task', {}).get('output', {}).get('config', {}).copy()

        return output_config
