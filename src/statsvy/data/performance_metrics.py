"""Performance metrics collected during scan operations.

This module defines immutable data structures for tracking application
performance metrics. Currently tracks memory usage; extensible for
additional metrics like CPU time, I/O statistics, etc.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerformanceMetrics:
    """Immutable container for performance statistics during a scan.

    Tracks peak memory usage during scan. Future metrics can be added
    as new fields (e.g., cpu_time_seconds, files_read_per_second, etc.).

    Attributes:
        peak_memory_bytes: Peak memory usage in bytes during the scan.
    """

    peak_memory_bytes: int
