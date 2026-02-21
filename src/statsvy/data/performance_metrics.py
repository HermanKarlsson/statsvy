"""Performance metrics collected during scan operations.

This module defines immutable data structures for tracking application
performance metrics. Tracks memory, I/O, and optional CPU profiling
statistics.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerformanceMetrics:
    """Immutable container for performance statistics during a scan.

    Tracks peak memory usage during scan. Also holds optional I/O and CPU
    statistics so a single formatter can present all performance results.

    Attributes:
        peak_memory_bytes: Peak memory usage in bytes during the scan.
        bytes_read: Total bytes read from disk by the scanner (when measured).
        io_mb_s: Computed I/O throughput in MiB/s (2^20) when available.
        cpu_seconds: Total process CPU time delta (user + system).
        cpu_user_seconds: Process user CPU time delta.
        cpu_system_seconds: Process system CPU time delta.
        cpu_percent_single_core: CPU usage normalized to one core.
            Formula: cpu_seconds / wall_seconds * 100.
            Can exceed 100% when multiple cores are actively used.
        cpu_percent_all_cores: CPU usage normalized by logical core count.
            Formula: cpu_percent_single_core / cpu_count.
    """

    peak_memory_bytes: int
    bytes_read: int = 0
    io_mb_s: float | None = None
    cpu_seconds: float | None = None
    cpu_user_seconds: float | None = None
    cpu_system_seconds: float | None = None
    cpu_percent_single_core: float | None = None
    cpu_percent_all_cores: float | None = None
