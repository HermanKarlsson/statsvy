"""Performance tracking for scan operations.

This module provides a PerformanceTracker class that measures and collects
performance metrics during scan operations. Currently tracks memory usage
via tracemalloc; designed to be extended with additional metrics.
"""

import tracemalloc

from statsvy.data.performance_metrics import PerformanceMetrics


class PerformanceTracker:
    """Tracks performance metrics during scan operations.

    This class encapsulates all performance tracking logic, providing a clean
    API for measuring application performance. Currently uses tracemalloc to
    track memory usage; future extensions can add CPU time, I/O statistics,
    cache hit rates, etc.

    Warning:
        Memory tracking using tracemalloc can add SIGNIFICANT overhead:
        - Small projects: 10-30% slower
        - Large projects with many files: 10-20x slower
        - The overhead comes from tracemalloc tracking every memory allocation

        Only enable performance tracking when you specifically need to profile
        memory usage. For timing information only, rely on the default execution
        time output which has negligible overhead.

    Note:
        - tracemalloc tracks Python memory allocations only (not C extensions)
        - Thread-safe for single-threaded use; not recommended for concurrent
          profiling without external synchronization
    """

    def __init__(self) -> None:
        """Initialize the performance tracker.

        Tracker is inactive until start() is called.
        """
        self._started = False

    def start(self) -> None:
        """Start performance tracking.

        Initializes tracemalloc and resets statistics. Should be called
        once before the operation to be tracked.

        Raises:
            RuntimeError: If tracker is already running.
        """
        if self._started:
            raise RuntimeError("PerformanceTracker is already running")

        tracemalloc.start()
        self._started = True

    def stop(self) -> PerformanceMetrics:
        """Stop performance tracking and return collected metrics.

        Returns:
            PerformanceMetrics object with collected statistics.

        Raises:
            RuntimeError: If tracker has not been started.
        """
        if not self._started:
            raise RuntimeError("PerformanceTracker has not been started")

        # Get peak memory usage (in bytes)
        _, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._started = False

        return PerformanceMetrics(peak_memory_bytes=peak_memory)

    def is_active(self) -> bool:
        """Check if tracker is currently active.

        Returns:
            True if tracking is running, False otherwise.
        """
        return self._started
