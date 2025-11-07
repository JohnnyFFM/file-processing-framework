# File Processing Framework

A simple, extensible Python framework for processing files in multiple formats (CSV, XML, JSON).

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### CLI Usage

```bash
# Process a CSV file
python main.py \
    --input file_processing_framework/examples/sample_data/sales_data.csv \
    --task demo \
    --config file_processing_framework/examples/sample_configs/csv_with_header.yaml \
    --output-dir ./output
```

### GUI Usage

```bash
# Launch the GUI
python main_gui.py
```

The GUI provides a simple interface:
1. Task is pre-selected with auto-linked config
2. Browse for input files (supports multiple selection)
3. Browse for output directory
4. Click "Run Task" and watch the progress

## Features

- **Multiple File Formats**: CSV, XML, JSON support
- **Format Auto-Detection**: Encoding, separators, number formats, dates
- **Task-Centric Design**: Tasks define all processing requirements
- **Simple Loop Processing**: N inputs → N outputs (1:1 mapping)
- **Both CLI and GUI**: Command-line and Tkinter interfaces
- **Extensible**: Easy to add new tasks and file formats
- **Python 3.11+**: Modern Python features

## Core Concept

```
Input:  [file1.csv, file2.csv, file3.csv]
        ↓ (all same format)
Loop:   Process each file with same task
        ↓
Output: [output1.json, output2.json, output3.json]
```

**Key Principles:**
- All input files must be the same format
- Task processes one file at a time
- N inputs → N outputs (1:1 mapping)
- Output format defined in config

## Configuration

Configuration files use a task-centric structure:

```yaml
task:
  name: demo
  description: "Simple demo task"

  input:
    format: csv
    config:
      has_header: true
      separator: ","

  parameters:
    output_suffix: "processed"

  output:
    format: json
    config:
      indent: 2
```

## Documentation

**Complete documentation:** [`docs/FRAMEWORK_DOCUMENTATION.md`](docs/FRAMEWORK_DOCUMENTATION.md)

The comprehensive documentation includes:
- Architecture overview
- Configuration details
- CLI and GUI usage
- How to extend the framework
- Examples and recipes
- Project structure

## Project Structure

```
file_processing_framework/
├── core/           # Core abstractions (Task, DataModel, Runner)
├── formats/        # Format detection and parsing
├── loaders/        # File loaders (CSV, JSON, XML)
├── writers/        # File writers (CSV, JSON, XML)
├── tasks/          # Processing tasks
├── config/         # Configuration management
├── cli/            # Command-line interface
├── gui/            # Graphical interface
└── examples/       # Sample data and configs

docs/               # Documentation
main.py             # CLI entry point
main_gui.py         # GUI entry point
```

## Extending the Framework

### Add a New Task

```python
# tasks/my_task.py
from ..core.task import Task

class MyTask(Task):
    def execute(self, data_model, params, input_filename):
        # Your processing logic
        processed_data = self._process(data_model)
        output_name = f"{input_filename}_processed"
        return processed_data, output_name
```

Register in `cli/main.py` and `gui/main_window.py`.

See [`docs/FRAMEWORK_DOCUMENTATION.md`](docs/FRAMEWORK_DOCUMENTATION.md) for complete extension guide.

## Requirements

- Python 3.11+
- pyyaml
- lxml
- xmltodict
- python-dateutil
- chardet

## Examples

**Process multiple files:**
```bash
python main.py \
    --input file1.csv file2.csv file3.csv \
    --task demo \
    --config config.yaml \
    --output-dir ./output
```

**Override format settings:**
```bash
python main.py \
    --input data.csv \
    --task demo \
    --output-dir ./output \
    --separator ";" \
    --decimal ","
```

More examples in [`docs/FRAMEWORK_DOCUMENTATION.md`](docs/FRAMEWORK_DOCUMENTATION.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with simplicity and extensibility in mind.** 🚀
