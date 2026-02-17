"""Path resolution utilities for target directory determination."""

import json
import os
from pathlib import Path

from rich.text import Text

from statsvy.utils.console import console


class PathResolver:
    """Resolves target directory paths for scanning operations."""

    @staticmethod
    def get_target_directory(provided_dir: str | None) -> Path:
        """Determine the target directory for scanning.

        If no directory is provided, attempts to load from .statsvy/project.json.
        Falls back to current working directory with a warning if neither is
        available.

        Args:
            provided_dir: The directory path provided by the user, or None.

        Returns:
            The Path object representing the target directory.

        Raises:
            PermissionError: If the provided directory is not writable.
            json.JSONDecodeError: If the project file contains invalid JSON.
            KeyError: If the project file does not define a "path" key.
        """
        if provided_dir:
            return PathResolver._validate_provided_directory(provided_dir)

        # Try to load from project file
        project_path = PathResolver._load_from_project_file()
        if project_path is not None:
            return project_path

        # Fallback to current directory
        console.print(
            Text(
                "Warning: No directory provided. Scanning current directory.",
                style="yellow",
            )
        )
        return Path.cwd()

    @staticmethod
    def _validate_provided_directory(provided_dir: str) -> Path:
        """Validate that the provided directory exists and is writable.

        Args:
            provided_dir: Directory path to validate.

        Returns:
            Path object for the validated directory.

        Raises:
            PermissionError: If the directory is not writable.
        """
        if not os.access(provided_dir, mode=os.W_OK):
            raise PermissionError(f"Directory '{provided_dir}' is not writable")
        return Path(provided_dir)

    @staticmethod
    def _load_from_project_file() -> Path | None:
        """Load project path from .statsvy/project.json if it exists.

        Returns:
            Path from project file, or None if file doesn't exist.

        Raises:
            json.JSONDecodeError: If the project file contains invalid JSON.
            KeyError: If the project file does not define a "path" key.
        """
        project_file = Path(".statsvy/project.json")
        if not project_file.exists():
            return None

        with open(project_file) as f:
            data = json.load(f)
            return Path(data["path"])
