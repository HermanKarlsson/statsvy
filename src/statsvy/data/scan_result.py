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
    bytes_read: int = 0
    # Optional per-file data populated by Scanner to avoid re-reading files.
    # Keys are file paths and values contain precomputed metadata used by
    # Analyzer (e.g. text, line count). This field is optional to preserve
    # backward compatibility for tests that construct ScanResult manually.
    file_data: dict[Path, dict[str, object]] | None = None
