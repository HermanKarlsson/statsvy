"""File analysis configuration data model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FilesConfig:
    """File-level analysis settings.

    Duplicate detection is now a core behaviour and cannot be disabled.
    The configuration keeps only the threshold for when to compute hashes.
    """

    duplicate_threshold_bytes: int
    find_large_files: bool
    large_file_threshold_mb: int
