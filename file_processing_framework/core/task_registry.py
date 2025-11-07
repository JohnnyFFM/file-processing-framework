"""
Task Registry - Auto-discovers and loads tasks as plugins.

Tasks are organized in subdirectories under tasks/ with the following structure:
    tasks/
    ├── my_task/
    │   ├── task.py       # Contains the Task class
    │   └── config.yaml   # Task configuration (optional)

The registry automatically discovers all tasks at startup.
"""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, Optional, Type
from .task import Task

logger = logging.getLogger(__name__)


class TaskRegistry:
    """
    Discovers and manages tasks as plugins.

    Tasks are automatically loaded from subdirectories in the tasks/ folder.
    Each task must have a task.py file containing a class that inherits from Task.
    """

    def __init__(self, tasks_dir: Optional[Path] = None):
        """
        Initialize the task registry.

        Args:
            tasks_dir: Path to tasks directory (defaults to tasks/ in framework)
        """
        if tasks_dir is None:
            # Default to tasks/ directory in the framework
            framework_root = Path(__file__).parent.parent
            tasks_dir = framework_root / 'tasks'

        self.tasks_dir = Path(tasks_dir)
        self._tasks: Dict[str, Type[Task]] = {}
        self._configs: Dict[str, Path] = {}
        self._discover_tasks()

    def _discover_tasks(self) -> None:
        """
        Discover all tasks in the tasks directory.

        Each subdirectory in tasks/ is scanned for:
        - task.py: Python file containing a Task class
        - config.yaml: Optional configuration file
        """
        if not self.tasks_dir.exists():
            logger.warning(f"Tasks directory not found: {self.tasks_dir}")
            return

        logger.info(f"Discovering tasks in: {self.tasks_dir}")

        for task_dir in self.tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue

            # Skip __pycache__ and other special directories
            if task_dir.name.startswith('_'):
                continue

            self._load_task(task_dir)

        logger.info(f"Discovered {len(self._tasks)} task(s): {', '.join(self._tasks.keys())}")

    def _load_task(self, task_dir: Path) -> None:
        """
        Load a task from a directory.

        Args:
            task_dir: Path to task directory
        """
        task_file = task_dir / 'task.py'
        config_file = task_dir / 'config.yaml'

        if not task_file.exists():
            logger.warning(f"Skipping {task_dir.name}: task.py not found")
            return

        try:
            # Build module name: file_processing_framework.tasks.task_name.task
            module_name = f"file_processing_framework.tasks.{task_dir.name}.task"

            # Import the module
            module = importlib.import_module(module_name)

            # Find the Task class in the module
            task_class = self._find_task_class(module)

            if task_class is None:
                logger.warning(f"Skipping {task_dir.name}: No Task class found in task.py")
                return

            # Register the task
            task_name = task_dir.name
            self._tasks[task_name] = task_class

            # Register config if exists
            if config_file.exists():
                self._configs[task_name] = config_file
                logger.debug(f"Loaded task '{task_name}' with config")
            else:
                logger.debug(f"Loaded task '{task_name}' (no config file)")

        except Exception as e:
            logger.error(f"Failed to load task from {task_dir.name}: {e}")

    def _find_task_class(self, module) -> Optional[Type[Task]]:
        """
        Find the Task class in a module.

        Args:
            module: Imported module

        Returns:
            Task class if found, None otherwise
        """
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Check if it's a Task subclass (but not Task itself)
            if issubclass(obj, Task) and obj is not Task:
                return obj
        return None

    def get_task(self, task_name: str) -> Type[Task]:
        """
        Get a task class by name.

        Args:
            task_name: Name of the task (directory name)

        Returns:
            Task class

        Raises:
            ValueError: If task not found
        """
        if task_name not in self._tasks:
            available = ', '.join(self._tasks.keys())
            raise ValueError(
                f"Unknown task '{task_name}'. Available tasks: {available}"
            )
        return self._tasks[task_name]

    def get_task_config(self, task_name: str) -> Optional[Path]:
        """
        Get the config file path for a task.

        Args:
            task_name: Name of the task

        Returns:
            Path to config file, or None if no config exists
        """
        return self._configs.get(task_name)

    def list_tasks(self) -> Dict[str, Dict[str, any]]:
        """
        List all available tasks with metadata.

        Returns:
            Dict mapping task name to metadata
        """
        tasks_info = {}
        for task_name, task_class in self._tasks.items():
            tasks_info[task_name] = {
                'class': task_class.__name__,
                'description': task_class.__doc__.strip() if task_class.__doc__ else 'No description',
                'has_config': task_name in self._configs,
                'config_path': str(self._configs[task_name]) if task_name in self._configs else None
            }
        return tasks_info

    def get_all_tasks(self) -> Dict[str, Type[Task]]:
        """
        Get all registered tasks.

        Returns:
            Dict mapping task name to Task class
        """
        return self._tasks.copy()

    def get_all_configs(self) -> Dict[str, Path]:
        """
        Get all registered task configs.

        Returns:
            Dict mapping task name to config Path
        """
        return self._configs.copy()
