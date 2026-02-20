"""Performance metrics collected during scan operations.

This module defines immutable data structures for tracking application
performance metrics. Currently tracks memory usage; extensible for
additional metrics like CPU time, I/O statistics, etc.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerformanceMetrics:
    """Immutable container for performance statistics during a scan.

    Tracks peak memory usage during scan. Also holds optional I/O
    statistics (bytes read and MB/s) so a single formatter can present
    both memory and I/O results.

    Attributes:
        peak_memory_bytes: Peak memory usage in bytes during the scan.
        bytes_read: Total bytes read from disk by the scanner (when measured).
        io_mb_s: Computed I/O throughput in MiB/s (2^20) when available.
    """

    peak_memory_bytes: int
    bytes_read: int = 0
    io_mb_s: float | None = None
