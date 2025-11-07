"""
Main entry point for CLI interface.

Usage:
    python main.py --input data.csv --task demo --output-format json --output-dir ./output
"""

from file_processing_framework.cli.main import main

if __name__ == '__main__':
    exit(main())
