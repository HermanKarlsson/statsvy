"""Project information extracted from configuration files.

This module defines an immutable data structure for representing extracted
metadata from project configuration files, without any business logic.
"""

from dataclasses import dataclass

from statsvy.data.dependency_info import DependencyInfo


@dataclass(frozen=True, slots=True)
class ProjectFileInfo:
    """Project information extracted from configuration files.

    Represents extracted data from one or more project configuration files.
    When multiple files are present (e.g., both pyproject.toml and
    requirements.txt), this represents the merged result.

    Attributes:
        name: Project name if found, None otherwise.
        dependencies: Dependency information if found, None otherwise.
        source_files: Tuple of source files that were read.
    """

    name: str | None
    dependencies: DependencyInfo | None
    source_files: tuple[str, ...]
