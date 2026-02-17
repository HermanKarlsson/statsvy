"""Single dependency in a project.

This module defines an immutable data structure for representing a single
dependency found in a project configuration file, without any business logic.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Dependency:
    """Single dependency in a project.

    Attributes:
        name: Package name (e.g., "click", "express").
        version: Version specification string (e.g., ">=8.0.0", "^1.2.3").
        category: Dependency category ("prod", "dev", "optional").
        source_file: Name of the file this dependency came from
            (e.g., "pyproject.toml", "requirements.txt").
    """

    name: str
    version: str
    category: str
    source_file: str
