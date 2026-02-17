"""Project configuration readers using strategy pattern.

This module provides readers for different project configuration file formats,
implementing a strategy pattern for extensible format support.
"""

from pathlib import Path
from typing import Protocol

from statsvy.data.project_info import ProjectFileInfo


class ProjectConfigReader(Protocol):
    """Protocol for reading project configuration files.

    Implementations read various project configuration formats
    (pyproject.toml, package.json, etc.) and extract project metadata
    and dependency information.
    """

    def read_project_info(self, path: Path) -> ProjectFileInfo:
        """Read project information from a configuration file.

        Args:
            path: Path to the configuration file.

        Returns:
            ProjectFileInfo containing extracted name, dependencies, and
            source files.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is invalid or cannot be parsed.
        """
        ...
