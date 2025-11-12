"""
Configuration loader.

Loads configuration from YAML, TOML, and JSON files.
"""

import json
from pathlib import Path
from typing import Dict, Any
import yaml

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python
    except ImportError:
        tomllib = None

from ..core.exceptions import ConfigError


class ConfigLoader:
    """
    Load configuration from various file formats.

    Supports:
    - YAML (.yaml, .yml)
    - TOML (.toml)
    - JSON (.json)
    """

    @staticmethod
    def load(filepath: str) -> Dict[str, Any]:
        """
        Load configuration file.

        Args:
            filepath: Path to configuration file

        Returns:
            dict: Configuration dictionary

        Raises:
            ConfigError: If file cannot be loaded or parsed
            FileNotFoundError: If file does not exist
        """
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")

        # Determine format from extension
        extension = path.suffix.lower()

        try:
            if extension in ['.yaml', '.yml']:
                return ConfigLoader._load_yaml(filepath)
            elif extension == '.toml':
                return ConfigLoader._load_toml(filepath)
            elif extension == '.json':
                return ConfigLoader._load_json(filepath)
            else:
                raise ConfigError(f"Unsupported config file format: {extension}")

        except Exception as e:
            if isinstance(e, (ConfigError, FileNotFoundError)):
                raise
            raise ConfigError(f"Failed to load config file {filepath}: {e}")

    @staticmethod
    def _load_yaml(filepath: str) -> Dict[str, Any]:
        """
        Load YAML configuration file.

        Args:
            filepath: Path to YAML file

        Returns:
            dict: Configuration

        Raises:
            ConfigError: If YAML is invalid
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if config is None:
                return {}

            if not isinstance(config, dict):
                raise ConfigError(f"YAML config must be a dictionary, got {type(config)}")

            return config

        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {filepath}: {e}")

    @staticmethod
    def _load_toml(filepath: str) -> Dict[str, Any]:
        """
        Load TOML configuration file.

        Args:
            filepath: Path to TOML file

        Returns:
            dict: Configuration

        Raises:
            ConfigError: If TOML is invalid or tomllib not available
        """
        if tomllib is None:
            raise ConfigError(
                "TOML support requires Python 3.11+ or 'tomli' package. "
                "Install with: pip install tomli"
            )

        try:
            with open(filepath, 'rb') as f:
                config = tomllib.load(f)

            return config

        except Exception as e:
            raise ConfigError(f"Invalid TOML in {filepath}: {e}")

    @staticmethod
    def _load_json(filepath: str) -> Dict[str, Any]:
        """
        Load JSON configuration file.

        Args:
            filepath: Path to JSON file

        Returns:
            dict: Configuration

        Raises:
            ConfigError: If JSON is invalid
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)

            if not isinstance(config, dict):
                raise ConfigError(f"JSON config must be an object, got {type(config)}")

            return config

        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {filepath}: {e}")

    @staticmethod
    def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.

        Override values take precedence over base values.
        Nested dicts are merged recursively.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            dict: Merged configuration

        Examples:
            >>> base = {'a': 1, 'b': {'c': 2, 'd': 3}}
            >>> override = {'b': {'d': 4}, 'e': 5}
            >>> ConfigLoader.merge_configs(base, override)
            {'a': 1, 'b': {'c': 2, 'd': 4}, 'e': 5}
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                result[key] = ConfigLoader.merge_configs(result[key], value)
            else:
                # Override value
                result[key] = value

        return result

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """
        Get default configuration.

        Returns:
            dict: Default configuration with safe defaults

        Note:
            This is used when no config file is provided.
            New structure: task-centric with input/output format defined.
        """
        return {
            'task': {
                'name': 'demo',
                'description': 'Simple demo task',
                'input': {
                    'format': 'csv',
                    'config': {
                        'has_header': True,
                        'separator': ',',
                        'decimal_separator': '.',
                        'thousands_separator': ',',
                        'encoding': 'utf-8',
                        'parse_values': True
                    }
                },
                'parameters': {
                    'config': {
                        'csv': {
                            'has_header': True,
                            'separator': ',',
                            'decimal_separator': '.',
                            'thousands_separator': ',',
                            'encoding': 'utf-8',
                            'parse_values': True
                        },
                        'json': {
                            'encoding': 'utf-8'
                        },
                        'xml': {
                            'encoding': 'utf-8'
                        }
                    }
                },
                'output': {
                    'format': 'json',
                    'config': {
                        'indent': 2,
                        'sort_keys': False,
                        'ensure_ascii': False,
                        'encoding': 'utf-8'
                    }
                }
            }
        }

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure.

        Args:
            config: Configuration to validate

        Returns:
            bool: True if valid

        Raises:
            ConfigError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ConfigError("Configuration must be a dictionary")

        # Validate task section
        if 'task' not in config:
            raise ConfigError("Configuration must have 'task' section")

        task_config = config['task']

        # Validate input format
        if 'input' not in task_config:
            raise ConfigError("Task configuration must have 'input' section")

        if 'format' not in task_config['input']:
            raise ConfigError("Task input must specify 'format' (csv, json, or xml)")

        valid_formats = ['csv', 'json', 'xml']
        input_format = task_config['input']['format']
        if input_format not in valid_formats:
            raise ConfigError(f"Invalid input format '{input_format}'. Must be one of: {', '.join(valid_formats)}")

        # Validate output format
        if 'output' not in task_config:
            raise ConfigError("Task configuration must have 'output' section")

        if 'format' not in task_config['output']:
            raise ConfigError("Task output must specify 'format' (csv, json, or xml)")

        output_format = task_config['output']['format']
        if output_format not in valid_formats:
            raise ConfigError(f"Invalid output format '{output_format}'. Must be one of: {', '.join(valid_formats)}")

        return True
