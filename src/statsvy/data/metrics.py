"""Metrics data model for analysis output."""

import datetime
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from statsvy.data.project_info import DependencyInfo


@dataclass(frozen=True, slots=True)
class Metrics:
    """Represent collected statistics and metadata for a project analysis.

    Attributes:
        name: Identifier for the project or analysis run.
        path: Filesystem path to the analyzed directory.
        timestamp: Point in time when the analysis was performed.
        total_files: Total number of scanned files.
        total_size_bytes: Cumulative size of all files in bytes.
        total_size_kb: Total size of all files in kilobytes.
        total_size_mb: Total size of all files in megabytes.
        lines_by_lang: Mapping of language names to their
                respective line counts.
        comment_lines_by_lang: Mapping of language names to their respective
            comment line counts.
        blank_lines_by_lang: Mapping of language names to their respective
            blank line counts.
        comment_lines: Total number of comment lines across all scanned files.
        blank_lines: Total number of blank lines across all scanned files.
        total_lines: Total number of lines across all scanned files.
        dependencies: Dependency analysis information if available.
    """

    name: str
    path: Path
    timestamp: datetime.datetime
    total_files: int
    total_size_bytes: int
    total_size_kb: int
    total_size_mb: int
    lines_by_lang: Mapping[str, int]
    comment_lines_by_lang: Mapping[str, int]
    blank_lines_by_lang: Mapping[str, int]
    lines_by_category: Mapping[str, int]
    comment_lines: int
    blank_lines: int
    total_lines: int
    dependencies: DependencyInfo | None = None
