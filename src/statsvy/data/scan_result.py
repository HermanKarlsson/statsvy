"""Scan result data model for directory traversal."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ScanResult:
    """Represent the raw result of a directory traversal.

    Attributes:
        total_files: Number of files discovered and included in the scan.
        total_size_bytes: Cumulative size of all discovered files in bytes.
        scanned_files: List of paths for every file that was scanned.
    """

    total_files: int
    total_size_bytes: int
    scanned_files: tuple[Path, ...]
    duplicate_files: tuple[Path, ...] = ()
