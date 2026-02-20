"""Scan configuration data model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScanConfig:
    """File system scanning settings.

    Attributes:
        min_file_size_mb: Minimum file size (in MB) to include in the scan.
            Files smaller than this will be skipped when scanning.
    """

    follow_symlinks: bool
    max_depth: int
    min_file_size_mb: float
    max_file_size_mb: float
    respect_gitignore: bool
    include_hidden: bool
    timeout_seconds: int
    ignore_patterns: tuple[str, ...]
    binary_extensions: tuple[str, ...]
