"""
CLI interface for the file processing framework.

Provides command-line interface using argparse.
"""

import argparse
import sys
from pathlib import Path
from typing import List
from ..core.runner import TaskRunner
from ..core.exceptions import FrameworkException
from ..core.task_registry import TaskRegistry


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='File Processing Framework - Process files in various formats (CSV, XML, JSON)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single CSV file (output format from config)
  python -m file_processing_framework.cli.main --input data.csv --task demo --config config.yaml --output-dir ./output

  # Process multiple files (loop processing)
  python -m file_processing_framework.cli.main --input file1.csv file2.csv file3.csv --task demo --config config.yaml --output-dir ./output

  # Override config with CLI parameters
  python -m file_processing_framework.cli.main --input data.csv --config config.yaml --task demo --output-dir ./output --separator ";" --decimal ","

  # Without config file (uses defaults)
  python -m file_processing_framework.cli.main --input data.csv --task demo --output-dir ./output
        """
    )

    # Required arguments
    parser.add_argument(
        '--input',
        '-i',
        nargs='+',
        required=True,
        help='Input file(s) to process (supports CSV, XML, JSON)'
    )

    parser.add_argument(
        '--task',
        '-t',
        required=True,
        default='demo',
        help='Task to execute (default: demo)'
    )

    parser.add_argument(
        '--output-dir',
        '-o',
        required=True,
        help='Output directory for processed files'
    )

    # Optional arguments
    parser.add_argument(
        '--config',
        '-c',
        help='Configuration file (YAML, TOML, or JSON)'
    )

    parser.add_argument(
        '--parameter-file',
        '-p',
        help='Parameter file for task (CSV, JSON, etc.)'
    )

    # CLI overrides for input formats
    parser.add_argument(
        '--separator',
        help='CSV separator/delimiter (overrides config)'
    )

    parser.add_argument(
        '--encoding',
        help='File encoding (overrides config)'
    )

    parser.add_argument(
        '--decimal',
        help='Decimal separator for numbers (overrides config)'
    )

    parser.add_argument(
        '--thousands',
        help='Thousands separator for numbers (overrides config)'
    )

    parser.add_argument(
        '--has-header',
        type=lambda x: x.lower() in ['true', '1', 'yes'],
        help='CSV has header row: true/false (overrides config)'
    )

    # Verbosity
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='File Processing Framework 1.0.0'
    )

    return parser.parse_args()


def build_cli_overrides(args: argparse.Namespace) -> dict:
    """
    Build configuration overrides from CLI arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        dict: Configuration overrides (new structure: task.input.config and task.parameters)
    """
    overrides = {}

    # Input overrides (new structure: task.input.config)
    if any([args.separator, args.encoding, args.decimal, args.thousands, args.has_header is not None]):
        if 'task' not in overrides:
            overrides['task'] = {}
        overrides['task']['input'] = {'config': {}}
        input_config = overrides['task']['input']['config']

        if args.separator:
            input_config['separator'] = args.separator

        if args.encoding:
            input_config['encoding'] = args.encoding

        if args.decimal:
            input_config['decimal_separator'] = args.decimal

        if args.thousands:
            input_config['thousands_separator'] = args.thousands

        if args.has_header is not None:
            input_config['has_header'] = args.has_header

    # Parameter file override (new structure: task.parameters)
    if args.parameter_file:
        if 'task' not in overrides:
            overrides['task'] = {}
        if 'parameters' not in overrides['task']:
            overrides['task']['parameters'] = {}
        overrides['task']['parameters']['parameter_file'] = args.parameter_file

    return overrides


def get_task_instance(task_name: str, registry: TaskRegistry):
    """
    Get task instance by name from registry.

    Args:
        task_name: Task name
        registry: TaskRegistry instance

    Returns:
        Task instance

    Raises:
        ValueError: If task not found
    """
    task_class = registry.get_task(task_name)
    return task_class()


def validate_inputs(input_files: List[str]) -> None:
    """
    Validate that input files exist.

    Args:
        input_files: List of input file paths

    Raises:
        FileNotFoundError: If any file doesn't exist
    """
    for filepath in input_files:
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Input file not found: {filepath}")


def main():
    """Main CLI entry point."""
    try:
        # Initialize task registry
        registry = TaskRegistry()

        # Parse arguments
        args = parse_arguments()

        # Validate inputs
        validate_inputs(args.input)

        # Get task instance
        task = get_task_instance(args.task, registry)

        # Get config file (use task's config if not provided)
        config_file = args.config
        if not config_file:
            task_config = registry.get_task_config(args.task)
            if task_config:
                config_file = str(task_config)

        # Build CLI overrides
        cli_overrides = build_cli_overrides(args)

        # Create and run TaskRunner
        runner = TaskRunner()

        print("Starting File Processing Framework")
        print(f"Input files ({len(args.input)}): {', '.join(args.input)}")
        print(f"Task: {args.task}")
        print(f"Output directory: {args.output_dir}")
        if config_file:
            print(f"Config file: {config_file}")
        print()

        output_files = runner.run(
            input_files=args.input,
            task=task,
            output_dir=args.output_dir,
            config_file=config_file,
            cli_overrides=cli_overrides if cli_overrides else None
        )

        print()
        print(f"Success! Generated {len(output_files)} file(s):")
        for output_file in output_files:
            print(f"  - {output_file}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except FrameworkException as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
