"""Performance metrics collected during scan operations.

This module defines immutable data structures for tracking application
performance metrics. Currently tracks memory usage; extensible for
additional metrics like CPU time, I/O statistics, etc.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerformanceMetrics:
    """Immutable container for performance statistics during a scan.

    Tracks peak memory usage and I/O statistics collected during the
    scan. New fields are optional and defaulted to preserve backwards
    compatibility with existing callers/tests.

    Attributes:
        peak_memory_bytes: Peak memory usage in bytes during the scan.
        total_bytes_read: Total application-level bytes read during the run.
        total_io_time_seconds: Cumulative wall-clock time spent in I/O reads.
        files_read_count: Number of file read operations recorded.
    """

    peak_memory_bytes: int
    total_bytes_read: int = 0
    total_io_time_seconds: float = 0.0
    files_read_count: int = 0
