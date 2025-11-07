# File Processing Framework - Complete Documentation

A simple, extensible Python framework for processing files in multiple formats (CSV, XML, JSON). Built with simplicity and extensibility in mind.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Configuration](#configuration)
5. [CLI Usage](#cli-usage)
6. [GUI Usage](#gui-usage)
7. [Extending the Framework](#extending-the-framework)
8. [Project Structure](#project-structure)
9. [Examples](#examples)

---

## Overview

### Features

- **Multiple File Formats**: Support for CSV, XML, and JSON
- **Format Auto-Detection**: Automatically detects separators, encodings, number formats, and date formats
- **Configurable Parsing**: Override auto-detection with manual configuration
- **Flexible Number Formats**: Handles different decimal and thousands separators (1,234.56 vs 1.234,56)
- **Flexible Date Formats**: Supports ISO, European, US, and custom date formats
- **Task-Centric Design**: Tasks define all processing requirements
- **Simple Loop Processing**: N inputs → N outputs (1:1 mapping)
- **Both CLI and GUI**: Command-line interface and Tkinter GUI
- **Python 3.11+**: Uses modern Python features

### Core Concept

**One task processes N files independently in a simple loop:**

```
Input:  [file1.csv, file2.csv, file3.csv]
        ↓ (all same format)
Loop:   Process each file with same task
        ↓
Output: [output1.json, output2.json, output3.json]
```

**Key Principles:**
- All input files must be the same format (validated)
- Task processes one file at a time
- N inputs → N outputs (1:1 mapping)
- No merging, no combining
- Output format defined in config (not user-selectable)

### Requirements

- Python 3.11+
- pyyaml
- lxml
- xmltodict
- python-dateutil
- chardet

---

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Test with CLI

```bash
# Process a single CSV file to JSON
python main.py \
    --input file_processing_framework/examples/sample_data/sales_data.csv \
    --task demo \
    --config file_processing_framework/examples/sample_configs/csv_with_header.yaml \
    --output-dir ./output

# Check the output
ls ./output
# You should see: sales_data_processed.json
```

### Test with GUI

```bash
# Launch the GUI
python main_gui.py
```

**GUI Workflow:**
1. **Task is pre-selected** (DemoTask) with auto-linked config
2. **Browse for input files** - select one or multiple CSV files
3. **Browse for output directory**
4. **Click "Run Task"** - watch progress in the log area

The GUI shows task information including input format, output format, and description.

---

## Architecture

### Design Philosophy

**Simple and straightforward - no complex pipelines, no unnecessary abstractions.**

```
Input Files → Loader → DataModel → Task → DataModel → Writer → Output Files
                ↑                                         ↑
           FormatDetector                          ConfigLoader
```

### Processing Flow

```
TaskRunner.run():
  For each input file:
    1. Validate file format matches config
    2. Select appropriate Loader
    3. Load file → DataModel
    4. Execute task(DataModel, params, input_filename)
    5. Get output DataModel and filename
    6. Select appropriate Writer
    7. Write DataModel → output file
    8. Log progress (file X of N)
```

### Core Components

**DataModel** - Unified data wrapper (dict/list)
```python
class DataModel:
    data: Union[dict, list]  # Plain Python structures
    metadata: dict
```

**Task** - Abstract processing task
```python
class Task(ABC):
    def execute(
        data_model: DataModel,
        params: dict,
        input_filename: str
    ) -> Tuple[DataModel, str]
```

**FileLoader** - Abstract file loader
```python
class FileLoader(ABC):
    def load(filepath: str, config: dict) -> DataModel
```

**FileWriter** - Abstract file writer
```python
class FileWriter(ABC):
    def write(data_model: DataModel, filepath: str, config: dict) -> None
```

**TaskRunner** - Main orchestrator
- Loads configuration
- Validates input files
- Coordinates loading, processing, writing
- Shows loop progress

---

## Configuration

### Configuration Structure (Task-Centric)

All configuration is organized under the `task` section:

```yaml
task:
  name: demo
  description: "Simple demo task for CSV processing"

  input:
    format: csv                    # All input files must match this
    config:
      has_header: true
      separator: ","
      decimal_separator: "."
      thousands_separator: ","
      encoding: utf-8
      parse_values: true

  parameters:
    add_processed_flag: true
    output_suffix: "processed"

  output:
    format: json                   # Output format (REQUIRED in config)
    config:
      indent: 2
      sort_keys: false
      encoding: utf-8
```

### Configuration Sections

**`task.name`** - Task identifier

**`task.description`** - Human-readable description (shown in GUI)

**`task.input.format`** - Expected input format (`csv`, `json`, or `xml`)

**`task.input.config`** - Format-specific input settings:
- **CSV**: `has_header`, `separator`, `decimal_separator`, `thousands_separator`, `encoding`, `columns`
- **JSON**: `encoding`
- **XML**: `encoding`

**`task.parameters`** - Task-specific parameters (passed to task.execute())

**`task.output.format`** - Output format (REQUIRED - `csv`, `json`, or `xml`)

**`task.output.config`** - Format-specific output settings:
- **CSV**: `separator`, `has_header`, `decimal_separator`, `thousands_separator`, `encoding`
- **JSON**: `indent`, `sort_keys`, `encoding`
- **XML**: `root_element`, `row_element`, `encoding`

### Sample Configurations

**Example 1: CSV with headers → JSON**
```yaml
task:
  name: demo
  description: "Simple demo task for CSV processing"

  input:
    format: csv
    config:
      has_header: true
      separator: ","
      decimal_separator: "."
      encoding: utf-8

  output:
    format: json
    config:
      indent: 2
```

**Example 2: CSV without headers → CSV with headers**
```yaml
task:
  name: demo
  description: "Process CSV files without headers"

  input:
    format: csv
    config:
      has_header: false
      columns: ["name", "age", "city", "salary"]
      separator: ","

  output:
    format: csv
    config:
      has_header: true
      separator: ","
```

**Example 3: European CSV → US CSV**
```yaml
task:
  name: demo
  description: "Convert European format to US format"

  input:
    format: csv
    config:
      has_header: true
      separator: ";"
      decimal_separator: ","
      thousands_separator: "."

  output:
    format: csv
    config:
      separator: ","
      decimal_separator: "."
      thousands_separator: ","
```

### Configuration File Formats

Configurations can be in **YAML**, **TOML**, or **JSON** format:

```bash
# YAML
--config config.yaml

# TOML
--config config.toml

# JSON
--config config.json
```

### CLI Configuration Overrides

Override specific input format settings from CLI:

```bash
python main.py \
    --input data.csv \
    --task demo \
    --output-dir ./output \
    --separator ";" \
    --decimal "," \
    --encoding "utf-8"
```

CLI overrides are applied to `task.input.config` section.

---

## CLI Usage

### Basic Syntax

```bash
python main.py \
    --input <file(s)> \
    --task <task_name> \
    --output-dir <directory> \
    [--config <config_file>] \
    [--separator <sep>] \
    [--encoding <enc>] \
    [--decimal <sep>]
```

### CLI Arguments

**Required:**
- `--input`, `-i` - Input file(s) (one or more)
- `--task`, `-t` - Task name to execute (e.g., `demo`)
- `--output-dir`, `-o` - Output directory path

**Optional:**
- `--config`, `-c` - Configuration file (YAML/TOML/JSON)
- `--separator`, `-s` - CSV separator (overrides config)
- `--encoding`, `-e` - File encoding (overrides config)
- `--decimal`, `-d` - Decimal separator (overrides config)
- `--thousands` - Thousands separator (overrides config)
- `--no-header` - CSV has no header (overrides config)

### Examples

**Process single file:**
```bash
python main.py \
    --input data.csv \
    --task demo \
    --config config.yaml \
    --output-dir ./output
```

**Process multiple files (loop):**
```bash
python main.py \
    --input file1.csv file2.csv file3.csv \
    --task demo \
    --config config.yaml \
    --output-dir ./output
```

**Override input format settings:**
```bash
python main.py \
    --input data.csv \
    --task demo \
    --output-dir ./output \
    --separator ";" \
    --decimal "," \
    --encoding "utf-8"
```

**Process all CSV files in directory:**
```bash
# Using shell expansion
python main.py \
    --input data/*.csv \
    --task demo \
    --config config.yaml \
    --output-dir ./output
```

### Output

CLI logs processing progress:
```
Loading configuration from: config.yaml
Processing file 1 of 3: file1.csv
Loaded 150 records
Task executed: DemoTask
Output written: ./output/file1_processed.json
Processing file 2 of 3: file2.csv
...
Completed successfully!
```

---

## GUI Usage

### Launching the GUI

```bash
python main_gui.py
```

### GUI Layout

The GUI follows a **task-first approach** with 4 steps:

```
┌──────────────────────────────────────────────────┐
│  File Processing Framework                       │
├──────────────────────────────────────────────────┤
│                                                  │
│  STEP 1: SELECT TASK                            │
│  ────────────────────────────────────────────   │
│  Task:         [DemoTask          ▼]            │
│  Description:  Simple demo task for CSV...       │
│  Input Format: CSV                               │
│  Output Format: JSON                             │
│                                                  │
│  STEP 2: CONFIGURATION                          │
│  ────────────────────────────────────────────   │
│  Config File:  csv_with_header.yaml             │
│  (auto-linked to task)                          │
│                                                  │
│  STEP 3: INPUT FILES                            │
│  ────────────────────────────────────────────   │
│  Input File(s): [___________] [Browse]          │
│  (select one or multiple files)                 │
│                                                  │
│  Parameter File: [___________] [Browse]         │
│  (optional - single parameter file)             │
│                                                  │
│  STEP 4: OUTPUT                                 │
│  ────────────────────────────────────────────   │
│  Output Dir:    [___________] [Browse]          │
│  (output format from config)                    │
│                                                  │
│  ────────────────────────────────────────────   │
│  [         Run Task         ]                   │
│                                                  │
│  Status: Ready                                  │
│  ────────────────────────────────────────────   │
│  Log Output:                                    │
│  ┌──────────────────────────────────────────┐  │
│  │ Processing file 1 of 3...                │  │
│  │ Loaded 150 records                       │  │
│  │ ...                                      │  │
│  └──────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### GUI Workflow

1. **Task Selection (STEP 1)**
   - Task is pre-selected (DemoTask)
   - Shows task description, input format, output format
   - Config file auto-links when task is selected

2. **Configuration (STEP 2)**
   - Config file is automatically loaded for selected task
   - Config field is read-only (auto-linked)
   - Maps tasks to their corresponding config files

3. **Input Files (STEP 3)**
   - Browse button allows **multiple file selection**
   - All selected files must match the task's input format
   - Optional parameter file can be selected
   - Displays file count if many files selected

4. **Output (STEP 4)**
   - Select output directory
   - Output format is shown but not selectable (comes from config)

5. **Run Task**
   - Click "Run Task" button
   - Processing happens in background thread (GUI stays responsive)
   - Log area shows progress: "Processing file X of N"
   - Success/error dialogs appear when complete

### GUI Features

- **Auto-config linking** - Config automatically loads when task is selected
- **Task information panel** - Shows input/output formats and description
- **Multi-file selection** - Process multiple files at once
- **Large log area** - 25 rows for detailed output
- **Progress tracking** - Shows which file is being processed
- **Background processing** - GUI remains responsive during long operations

---

## Extending the Framework

### Adding a New Task

Tasks define custom processing logic. Here's how to add one:

**1. Create task class** in `file_processing_framework/tasks/`:

```python
# tasks/my_custom_task.py
from pathlib import Path
from typing import Tuple
from ..core.task import Task
from ..core.data_model import DataModel

class MyCustomTask(Task):
    """
    Custom task that does something interesting.
    """

    def execute(
        self,
        data_model: DataModel,
        params: dict,
        input_filename: str
    ) -> Tuple[DataModel, str]:
        """
        Process the data.

        Args:
            data_model: Input data
            params: Parameters from config (task.parameters)
            input_filename: Original input filename

        Returns:
            (processed_data_model, output_filename)
        """
        # Access parameters
        threshold = params.get('threshold', 100)
        flag = params.get('flag', True)

        # Process data
        if isinstance(data_model.data, list):
            # Process list of dicts (CSV/JSON array)
            processed_rows = []
            for row in data_model.data:
                # Your processing logic
                processed_row = self._process_row(row, threshold)
                processed_rows.append(processed_row)

            processed_data = DataModel(processed_rows, data_model.metadata)
        else:
            # Process nested structure (JSON object/XML)
            processed_dict = self._process_dict(data_model.data)
            processed_data = DataModel(processed_dict, data_model.metadata)

        # Generate output filename
        file_stem = Path(input_filename).stem
        suffix = params.get('output_suffix', 'processed')
        output_name = f"{file_stem}_{suffix}"

        return processed_data, output_name

    def _process_row(self, row: dict, threshold: int) -> dict:
        """Custom row processing logic."""
        # Example: filter based on threshold
        if row.get('value', 0) > threshold:
            row['flag'] = 'HIGH'
        else:
            row['flag'] = 'LOW'
        return row

    def _process_dict(self, data: dict) -> dict:
        """Custom dict processing logic."""
        # Your logic here
        return data
```

**2. Register task in CLI** (`cli/main.py`):

```python
from ..tasks.demo_task import DemoTask
from ..tasks.my_custom_task import MyCustomTask

TASKS = {
    'demo': DemoTask,
    'custom': MyCustomTask,  # Add your task
}
```

**3. Register task in GUI** (`gui/main_window.py`):

```python
from ..tasks.demo_task import DemoTask
from ..tasks.my_custom_task import MyCustomTask

self.tasks = {
    'DemoTask': DemoTask,
    'MyCustomTask': MyCustomTask,  # Add your task
}

# Optionally add config mapping
self.task_configs = {
    'DemoTask': 'file_processing_framework/examples/sample_configs/csv_with_header.yaml',
    'MyCustomTask': 'file_processing_framework/examples/sample_configs/my_custom_config.yaml',
}
```

**4. Create config file** for your task:

```yaml
task:
  name: custom
  description: "My custom processing task"

  input:
    format: csv
    config:
      has_header: true
      separator: ","

  parameters:
    threshold: 100
    flag: true
    output_suffix: "custom"

  output:
    format: json
    config:
      indent: 2
```

### Adding a New File Format

To support a new file format (e.g., Parquet, Avro):

**1. Create Loader** (`loaders/newformat_loader.py`):

```python
from pathlib import Path
from ..core.loader import FileLoader
from ..core.data_model import DataModel

class NewFormatLoader(FileLoader):
    """Load NewFormat files into DataModel."""

    def load(self, filepath: str, config: dict) -> DataModel:
        """
        Load NewFormat file.

        Args:
            filepath: Path to file
            config: Config dict from task.input.config

        Returns:
            DataModel with loaded data
        """
        encoding = config.get('encoding', 'utf-8')

        # Load file
        with open(filepath, 'r', encoding=encoding) as f:
            # Parse file format
            data = self._parse_newformat(f, config)

        # Create metadata
        metadata = self._get_file_metadata(filepath, 'newformat')

        return DataModel(data, metadata)

    def _parse_newformat(self, file, config):
        """Parse the new format."""
        # Your parsing logic
        return []  # Return list of dicts or dict
```

**2. Create Writer** (`writers/newformat_writer.py`):

```python
from ..core.writer import FileWriter
from ..core.data_model import DataModel

class NewFormatWriter(FileWriter):
    """Write DataModel to NewFormat."""

    def write(
        self,
        data_model: DataModel,
        filepath: str,
        config: dict
    ) -> None:
        """
        Write data to NewFormat file.

        Args:
            data_model: Data to write
            filepath: Output file path
            config: Config dict from task.output.config
        """
        encoding = config.get('encoding', 'utf-8')

        with open(filepath, 'w', encoding=encoding) as f:
            # Write data in new format
            self._write_newformat(f, data_model.data, config)

    def _write_newformat(self, file, data, config):
        """Write data in the new format."""
        # Your writing logic
        pass
```

**3. Register in TaskRunner** (`core/runner.py`):

```python
from ..loaders.csv_loader import CsvLoader
from ..loaders.newformat_loader import NewFormatLoader
# ...

LOADERS = {
    '.csv': CsvLoader,
    '.newext': NewFormatLoader,  # Add loader
    # ...
}

from ..writers.csv_writer import CsvWriter
from ..writers.newformat_writer import NewFormatWriter
# ...

WRITERS = {
    'csv': CsvWriter,
    'newformat': NewFormatWriter,  # Add writer
    # ...
}
```

**4. Update validation** in `config/config_loader.py`:

```python
VALID_FORMATS = ['csv', 'json', 'xml', 'newformat']  # Add format
```

---

## Project Structure

```
file_processing_framework/
├── core/                       # Core abstractions
│   ├── __init__.py
│   ├── data_model.py           # DataModel wrapper
│   ├── task.py                 # Abstract Task base class
│   ├── loader.py               # Abstract FileLoader base class
│   ├── writer.py               # Abstract FileWriter base class
│   ├── runner.py               # TaskRunner orchestrator
│   └── exceptions.py           # Custom exceptions
│
├── formats/                    # Format handling utilities
│   ├── __init__.py
│   ├── number_parser.py        # Parse different number formats
│   ├── date_parser.py          # Parse different date formats
│   └── detector.py             # Auto-detect formats
│
├── loaders/                    # File format loaders
│   ├── __init__.py
│   ├── csv_loader.py           # CSV → DataModel
│   ├── json_loader.py          # JSON → DataModel
│   └── xml_loader.py           # XML → DataModel
│
├── writers/                    # File format writers
│   ├── __init__.py
│   ├── csv_writer.py           # DataModel → CSV
│   ├── json_writer.py          # DataModel → JSON
│   └── xml_writer.py           # DataModel → XML
│
├── tasks/                      # Processing tasks
│   ├── __init__.py
│   └── demo_task.py            # Example demo task
│
├── config/                     # Configuration management
│   ├── __init__.py
│   └── config_loader.py        # Load YAML/TOML/JSON configs
│
├── cli/                        # Command-line interface
│   ├── __init__.py
│   └── main.py                 # CLI argument parsing and execution
│
├── gui/                        # Graphical user interface
│   ├── __init__.py
│   └── main_window.py          # Tkinter GUI implementation
│
└── examples/                   # Example data and configs
    ├── sample_data/            # Sample input files
    │   ├── sales_data.csv
    │   ├── employees.json
    │   ├── products.xml
    │   └── data_no_header.csv
    └── sample_configs/         # Example configurations
        ├── csv_with_header.yaml
        ├── csv_no_header.yaml
        └── european_format.yaml

docs/                           # Documentation
└── FRAMEWORK_DOCUMENTATION.md  # This file

main.py                         # CLI entry point
main_gui.py                     # GUI entry point
requirements.txt                # Python dependencies
```

---

## Examples

### Example 1: Simple CSV → JSON

**Input** (`data.csv`):
```csv
name,age,city,salary
John,30,NYC,75000
Jane,25,LA,80000
```

**Config** (`config.yaml`):
```yaml
task:
  name: demo
  description: "Convert CSV to JSON"
  input:
    format: csv
    config:
      has_header: true
      separator: ","
  output:
    format: json
    config:
      indent: 2
```

**Command**:
```bash
python main.py \
    --input data.csv \
    --task demo \
    --config config.yaml \
    --output-dir ./output
```

**Output** (`data_processed.json`):
```json
[
  {
    "name": "John",
    "age": 30,
    "city": "NYC",
    "salary": 75000
  },
  {
    "name": "Jane",
    "age": 25,
    "city": "LA",
    "salary": 80000
  }
]
```

### Example 2: CSV Without Headers

**Input** (`data_no_header.csv`):
```csv
John,30,NYC,75000
Jane,25,LA,80000
```

**Config** (`csv_no_header.yaml`):
```yaml
task:
  name: demo
  description: "Process CSV without headers"
  input:
    format: csv
    config:
      has_header: false
      columns: ["name", "age", "city", "salary"]
      separator: ","
  output:
    format: csv
    config:
      has_header: true
      separator: ","
```

**Command**:
```bash
python main.py \
    --input data_no_header.csv \
    --task demo \
    --config csv_no_header.yaml \
    --output-dir ./output
```

**Output** (`data_no_header_demo.csv`):
```csv
name,age,city,salary
John,30,NYC,75000
Jane,25,LA,80000
```

### Example 3: European Format Conversion

**Input** (`european_data.csv`):
```csv
name;amount;date
John;1.234,56;31.12.2023
Jane;2.345,67;15.01.2024
```

**Config** (`european_format.yaml`):
```yaml
task:
  name: demo
  description: "Convert European CSV to US format"
  input:
    format: csv
    config:
      has_header: true
      separator: ";"
      decimal_separator: ","
      thousands_separator: "."
  output:
    format: csv
    config:
      separator: ","
      decimal_separator: "."
      thousands_separator: ","
```

**Command**:
```bash
python main.py \
    --input european_data.csv \
    --task demo \
    --config european_format.yaml \
    --output-dir ./output
```

**Output** (`european_data_converted.csv`):
```csv
name,amount,date
John,1234.56,31.12.2023
Jane,2345.67,15.01.2024
```

### Example 4: Processing Multiple Files

**Command**:
```bash
python main.py \
    --input file1.csv file2.csv file3.csv \
    --task demo \
    --config config.yaml \
    --output-dir ./output
```

**Output**:
```
Processing file 1 of 3: file1.csv
Loaded 100 records
Task executed: DemoTask
Output written: ./output/file1_processed.json

Processing file 2 of 3: file2.csv
Loaded 150 records
Task executed: DemoTask
Output written: ./output/file2_processed.json

Processing file 3 of 3: file3.csv
Loaded 200 records
Task executed: DemoTask
Output written: ./output/file3_processed.json

Completed successfully!
```

---

## Appendix

### Data Model Details

The `DataModel` class is a simple wrapper around Python's native data structures:

```python
class DataModel:
    def __init__(self, data: Union[dict, list], metadata: dict = None):
        self.data = data          # Plain dict or list
        self.metadata = metadata  # File info, format, etc.

    def get_rows(self) -> list[dict]:
        """Get data as list of dicts (for tabular data)."""
        if isinstance(self.data, list):
            return self.data
        return [self.data]

    def get_value(self, path: str, default: Any = None) -> Any:
        """Get nested value using dot notation."""
        # e.g., get_value("user.address.city")
        keys = path.split('.')
        value = self.data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default
```

**For tabular data (CSV, JSON arrays):**
```python
data_model.data = [
    {"name": "John", "age": 30},
    {"name": "Jane", "age": 25}
]
```

**For nested data (JSON objects, XML):**
```python
data_model.data = {
    "users": [
        {"name": "John", "age": 30}
    ],
    "metadata": {
        "version": "1.0"
    }
}
```

### Format Auto-Detection

The framework includes intelligent format auto-detection:

**Encoding Detection:**
- Uses `chardet` library
- Tries UTF-8, Latin-1, Windows-1252
- Falls back to system default

**CSV Separator Detection:**
- Analyzes first few lines
- Detects comma, semicolon, tab, pipe
- Scores candidates by consistency

**Number Format Detection:**
- Identifies decimal separator (. vs ,)
- Identifies thousands separator
- Handles formats like: 1,234.56 or 1.234,56

**Date Format Detection:**
- Tries common formats: ISO, European, US
- Supports fuzzy parsing
- Preserves original format if parsing fails

### Error Handling

The framework uses custom exceptions for clear error messages:

```python
# Configuration errors
ConfigError: "Configuration file not found: config.yaml"
ConfigError: "Invalid format 'xyz'. Must be one of: csv, json, xml"

# File errors
FileLoadError: "Failed to load file: data.csv"
FileWriteError: "Failed to write file: output.json"

# Task errors
TaskExecutionError: "Task failed: DemoTask"

# Validation errors
ValidationError: "File 'data.txt' does not match expected format 'csv'"
```

### Performance Notes

- **No pandas dependency** - Uses native Python structures for minimal overhead
- **Streaming not implemented** - Entire files loaded into memory
- **Suitable for small-to-medium files** - Recommend < 1GB per file
- **For large files** - Consider implementing streaming in custom loaders/writers

### Development Status

**Current Version:** 1.0

**Implemented:**
- CSV, JSON, XML support
- Task-centric configuration
- CLI and GUI interfaces
- Format auto-detection
- Number and date parsing
- Loop processing (N files → N outputs)
- Configuration validation

**Future Enhancements:**
- Additional file formats (Excel, Parquet, Avro)
- Streaming for large files
- Parallel processing option
- More built-in tasks
- Task chaining/composition
- Plugin system
- Unit tests

---

## License

This framework is provided as-is for educational and commercial use.

---

**Built with simplicity and extensibility in mind.** 🚀
