"""
GUI interface for the file processing framework.

Simple Tkinter-based GUI for file selection and processing.
Task-first approach: User selects task, then provides files.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import logging
from typing import List
from ..core.runner import TaskRunner
from ..core.exceptions import FrameworkException
from ..core.task_registry import TaskRegistry
from ..config.config_loader import ConfigLoader


class GUILogHandler(logging.Handler):
    """
    Custom logging handler that writes log messages to GUI text widget.
    """

    def __init__(self, log_callback):
        """
        Initialize handler.

        Args:
            log_callback: Function to call with log messages
        """
        super().__init__()
        self.log_callback = log_callback

    def emit(self, record):
        """
        Emit a log record.

        Args:
            record: LogRecord to emit
        """
        try:
            msg = self.format(record)
            self.log_callback(msg)
        except Exception:
            self.handleError(record)


class MainWindow:
    """
    Main GUI window for the file processing framework.

    Task-first approach:
    1. Select task
    2. Load config (optional, shows task requirements)
    3. Select input files
    4. Choose output directory
    5. Run
    """

    def __init__(self, root):
        """
        Initialize the main window.

        Args:
            root: Tk root window
        """
        self.root = root
        self.root.title("File Processing Framework")
        self.root.geometry("750x750")
        self.root.resizable(True, True)

        # Variables
        self.input_files = []
        self.config_file = None
        self.parameter_file = None
        self.current_config = None

        # Set default output directory
        self.default_output_dir = Path.cwd() / "output"
        self.default_output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = str(self.default_output_dir)

        # Initialize task registry (auto-discovers tasks)
        self.registry = TaskRegistry()
        self.tasks = self.registry.get_all_tasks()
        self.task_configs = {}

        # Build task name to config path mapping
        for task_name, config_path in self.registry.get_all_configs().items():
            self.task_configs[task_name] = str(config_path)

        self.config_loader = ConfigLoader()

        # Setup logging handler for capturing framework logs
        self.log_handler = None
        self._setup_logging_handler()

        # Create UI
        self._create_ui()

        # Center window
        self._center_window()

    def _create_ui(self):
        """Create the user interface."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        row = 0

        # Title
        title_label = ttk.Label(
            main_frame,
            text="File Processing Framework",
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 15))
        row += 1

        # === STEP 1: SELECT TASK ===
        step1_label = ttk.Label(main_frame, text="STEP 1: SELECT TASK", font=('Arial', 10, 'bold'))
        step1_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(5, 5))
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # Task Selection
        ttk.Label(main_frame, text="Task:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.task_var = tk.StringVar(value='DemoTask')
        task_combo = ttk.Combobox(
            main_frame,
            textvariable=self.task_var,
            values=list(self.tasks.keys()),
            state='readonly',
            width=47
        )
        task_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        task_combo.bind('<<ComboboxSelected>>', self._on_task_selected)
        row += 1

        # Task Info Display
        self.task_info_text = tk.Text(main_frame, height=3, width=50, wrap=tk.WORD, font=('Arial', 9))
        self.task_info_text.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.task_info_text.config(state='disabled')
        row += 1

        # === STEP 2: INPUT FILES ===
        step3_label = ttk.Label(main_frame, text="STEP 2: INPUT FILES", font=('Arial', 10, 'bold'))
        step3_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # Input Files
        ttk.Label(main_frame, text="Input File(s):").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)

        # Create frame for listbox and scrollbar
        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Listbox with scrollbar
        listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.input_listbox = tk.Listbox(
            listbox_frame,
            height=5,
            width=50,
            yscrollcommand=listbox_scrollbar.set,
            selectmode=tk.EXTENDED
        )
        listbox_scrollbar.config(command=self.input_listbox.yview)
        self.input_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Button frame for Add/Remove
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=2, pady=5)
        ttk.Button(button_frame, text="Add", command=self._browse_input, width=8).pack(pady=2)
        ttk.Button(button_frame, text="Remove", command=self._remove_input, width=8).pack(pady=2)
        row += 1

        ttk.Label(main_frame, text="(select one or multiple files)", font=('Arial', 8, 'italic')).grid(
            row=row, column=1, sticky=tk.W, padx=5
        )
        row += 1

        # Parameter File
        ttk.Label(main_frame, text="Parameter File:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.parameter_entry = ttk.Entry(main_frame, width=50)
        self.parameter_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(main_frame, text="Browse", command=self._browse_parameter).grid(row=row, column=2, pady=5)
        row += 1

        ttk.Label(main_frame, text="(optional - single parameter file for task)", font=('Arial', 8, 'italic')).grid(
            row=row, column=1, sticky=tk.W, padx=5
        )
        row += 1

        # === STEP 3: OUTPUT ===
        step4_label = ttk.Label(main_frame, text="STEP 3: OUTPUT", font=('Arial', 10, 'bold'))
        step4_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # Output Directory
        ttk.Label(main_frame, text="Output Dir:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.output_entry = ttk.Entry(main_frame, width=50)
        self.output_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(main_frame, text="Browse", command=self._browse_output).grid(row=row, column=2, pady=5)
        row += 1

        ttk.Label(main_frame, text="(output format from config)", font=('Arial', 8, 'italic')).grid(
            row=row, column=1, sticky=tk.W, padx=5
        )
        row += 1

        # Run Button
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1

        self.run_button = ttk.Button(
            main_frame,
            text="Run Task",
            command=self._run_process,
            style='Accent.TButton'
        )
        self.run_button.grid(row=row, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        row += 1

        # Status
        ttk.Label(main_frame, text="Status:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # Log Output
        ttk.Label(main_frame, text="Log Output:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 5)
        )
        row += 1

        # Scrolled text widget for log
        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            width=85,
            height=12,
            wrap=tk.WORD,
            font=('Courier', 9)
        )
        self.log_text.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(row, weight=1)
        row += 1

        # Configure style for accent button
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 11, 'bold'))

        # Set default output directory in entry
        self.output_entry.insert(0, str(self.default_output_dir))

        # Update task info and load config on startup
        self._on_task_selected()

    def _center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _on_task_selected(self, event=None):
        """Handle task selection change."""
        # Auto-load config file for selected task
        task_name = self.task_var.get()
        if task_name in self.task_configs:
            config_path = Path(self.task_configs[task_name])
            if config_path.exists():
                self.config_file = str(config_path)
                self._log(f"Auto-loaded config for {task_name}: {config_path.name}")
            else:
                self._log(f"Warning: Config file not found: {config_path}")

        self._update_task_info()

    def _update_task_info(self):
        """Update task information display."""
        # Load config to get task info
        if self.config_file:
            try:
                self.current_config = self.config_loader.load(self.config_file)
            except:
                self.current_config = self.config_loader.get_default_config()
        else:
            self.current_config = self.config_loader.get_default_config()

        # Get task info from config
        task_config = self.current_config.get('task', {})
        description = task_config.get('description', 'No description available')
        input_format = task_config.get('input', {}).get('format', 'unknown')
        output_format = task_config.get('output', {}).get('format', 'unknown')

        # Update info text
        info_text = f"Description: {description}\n"
        info_text += f"Input Format: {input_format.upper()}\n"
        info_text += f"Output Format: {output_format.upper()}"

        self.task_info_text.config(state='normal')
        self.task_info_text.delete('1.0', tk.END)
        self.task_info_text.insert('1.0', info_text)
        self.task_info_text.config(state='disabled')

    def _browse_input(self):
        """Browse for input files."""
        filetypes = [
            ('All Supported', '*.csv *.json *.xml'),
            ('CSV files', '*.csv'),
            ('JSON files', '*.json'),
            ('XML files', '*.xml'),
            ('All files', '*.*')
        ]

        filenames = filedialog.askopenfilenames(
            title="Select Input File(s)",
            filetypes=filetypes
        )

        if filenames:
            # Add new files to the list (avoid duplicates)
            for filename in filenames:
                if filename not in self.input_files:
                    self.input_files.append(filename)
                    self.input_listbox.insert(tk.END, Path(filename).name)
            self._log(f"Added {len(filenames)} input file(s)")

    def _remove_input(self):
        """Remove selected files from input list."""
        selected_indices = self.input_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "Please select file(s) to remove")
            return

        # Remove in reverse order to maintain indices
        for index in reversed(selected_indices):
            self.input_listbox.delete(index)
            del self.input_files[index]

        self._log(f"Removed {len(selected_indices)} file(s)")

    def _browse_parameter(self):
        """Browse for parameter file."""
        filetypes = [
            ('All Supported', '*.csv *.json *.xml *.txt *.yaml *.yml'),
            ('CSV files', '*.csv'),
            ('JSON files', '*.json'),
            ('XML files', '*.xml'),
            ('Text files', '*.txt'),
            ('YAML files', '*.yaml *.yml'),
            ('All files', '*.*')
        ]

        filename = filedialog.askopenfilename(
            title="Select Parameter File",
            filetypes=filetypes
        )

        if filename:
            self.parameter_file = filename
            self.parameter_entry.delete(0, tk.END)
            self.parameter_entry.insert(0, Path(filename).name)
            self._log(f"Selected parameter file: {Path(filename).name}")

    def _browse_output(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory"
        )

        if directory:
            self.output_dir = directory
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)
            self._log(f"Output directory: {directory}")

    def _run_process(self):
        """Run the processing workflow."""
        # Validate inputs
        if not self.input_files:
            messagebox.showerror("Error", "Please select at least one input file")
            return

        if not self.output_dir:
            messagebox.showerror("Error", "Please select an output directory")
            return

        # Disable run button
        self.run_button.config(state='disabled')
        self.status_var.set("Processing...")
        self._log("\n" + "="*75)
        self._log("Starting processing...")
        self._log("="*75)

        # Run in separate thread to avoid freezing GUI
        thread = threading.Thread(target=self._process_files, daemon=True)
        thread.start()

    def _process_files(self):
        """Process files (runs in separate thread)."""
        try:
            # Attach logging handler to capture framework logs
            self._attach_log_handler()

            # Get task instance
            task_name = self.task_var.get()
            task_class = self.tasks[task_name]
            task = task_class()

            # Create runner
            runner = TaskRunner()

            # Log parameters
            self._log(f"Task: {task_name}")
            self._log(f"Input files: {len(self.input_files)}")
            for i, f in enumerate(self.input_files, 1):
                self._log(f"  {i}. {Path(f).name}")
            if self.config_file:
                self._log(f"Config: {Path(self.config_file).name}")
            else:
                self._log("Config: Using defaults")
            if self.parameter_file:
                self._log(f"Parameter file: {Path(self.parameter_file).name}")
            self._log(f"Output directory: {self.output_dir}")
            self._log("")

            # Build overrides for parameter file
            cli_overrides = None
            if self.parameter_file:
                cli_overrides = {
                    'task': {
                        'parameters': {
                            'parameter_file': self.parameter_file
                        }
                    }
                }

            # Run processing
            output_files = runner.run(
                input_files=self.input_files,
                task=task,
                output_dir=self.output_dir,
                config_file=self.config_file if self.config_file else None,
                cli_overrides=cli_overrides
            )

            # Success
            self._log("")
            self._log("="*75)
            self._log(f"Success! Generated {len(output_files)} file(s):")
            for i, output_file in enumerate(output_files, 1):
                self._log(f"  {i}. {Path(output_file).name}")
            self._log("="*75)

            self.root.after(0, lambda: self.status_var.set("Completed successfully"))
            self.root.after(0, lambda: messagebox.showinfo(
                "Success",
                f"Processing completed!\n\nGenerated {len(output_files)} file(s) in:\n{self.output_dir}"
            ))

        except FrameworkException as e:
            self._log(f"\nERROR: {e}")
            self.root.after(0, lambda: self.status_var.set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        except Exception as e:
            self._log(f"\nUNEXPECTED ERROR: {e}")
            self.root.after(0, lambda: self.status_var.set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Unexpected Error", str(e)))

        finally:
            # Detach logging handler
            self._detach_log_handler()

            # Re-enable run button
            self.root.after(0, lambda: self.run_button.config(state='normal'))

    def _log(self, message: str):
        """
        Add message to log output.

        Args:
            message: Message to log
        """
        def append_text():
            self.log_text.insert(tk.END, message + '\n')
            self.log_text.see(tk.END)

        self.root.after(0, append_text)

    def _setup_logging_handler(self):
        """
        Setup logging handler to capture framework logs in GUI.
        """
        # Create handler with callback to _log
        self.log_handler = GUILogHandler(self._log)

        # Format: simple message without timestamp (GUI shows execution time already)
        formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        self.log_handler.setLevel(logging.INFO)

    def _attach_log_handler(self):
        """Attach the GUI log handler to root logger."""
        if self.log_handler:
            root_logger = logging.getLogger()
            root_logger.addHandler(self.log_handler)

    def _detach_log_handler(self):
        """Detach the GUI log handler from root logger."""
        if self.log_handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self.log_handler)


def main():
    """Main entry point for GUI."""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == '__main__':
    main()
