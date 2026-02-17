"""Project metadata management.

This module defines the data structure for storing project information
and tracking scan history.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from statsvy.data.git_info import GitInfo


@dataclass(frozen=True, slots=True)
class ProjectMeta:
    """Stores metadata about a tracked project.

    This dataclass holds essential information about a project being tracked
    by statsvy, including the project name, file system path, and scan history.

    Attributes:
        name: The name of the project (e.g., "my-app", "statsvy").
        path: The absolute or relative file system path to the project root.
        date_added: The date when the project was first added to tracking.
        last_scan: The timestamp of the most recent scan in ISO 8601 format
            (e.g., "2024-01-15T14:30:45").
        git_info: Basic Git repository metadata, if available.
    """

    name: str
    path: Path
    date_added: date
    last_scan: str | None = None
    git_info: GitInfo | None = None
