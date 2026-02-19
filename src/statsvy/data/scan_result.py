"""Scan result data model for directory traversal."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ScanResult:
    """Represent the raw result of a directory traversal.

    Attributes:
        total_files: Number of files discovered and included in the scan.
        total_size_bytes: Cumulative size of all discovered files in bytes.
        scanned_files: List of paths for every file that was scanned.
        duplicate_files: Tuple of paths that were detected as duplicates.
        file_contents: Optional read contents for scanned files (mapping
            Path -> text). When provided by the `Scanner`, analyzers may use
            these to avoid re-reading files from disk.
    """

    total_files: int
    total_size_bytes: int
    scanned_files: tuple[Path, ...]
    duplicate_files: tuple[Path, ...] = ()
    file_contents: Mapping[Path, str] | None = None
