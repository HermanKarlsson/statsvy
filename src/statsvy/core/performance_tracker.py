"""Performance tracking for scan operations.

This module provides a PerformanceTracker class that measures and collects
performance metrics during scan operations. Currently tracks memory usage
via tracemalloc and optional process CPU usage via resource.getrusage.
"""

import os
import resource
import tracemalloc
from time import perf_counter

from statsvy.data.performance_metrics import PerformanceMetrics


class PerformanceTracker:
    """Tracks performance metrics during scan operations.

    This class encapsulates all performance tracking logic, providing a clean
    API for measuring application performance. Uses tracemalloc to track
    memory usage and can optionally track process CPU usage.

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

    def __init__(self, *, track_memory: bool = True, track_cpu: bool = False) -> None:
        """Initialize the performance tracker.

        Args:
            track_memory: If True, collect peak memory via tracemalloc.
            track_cpu: If True, collect CPU deltas and CPU percentages.

        Tracker is inactive until start() is called.
        """
        self._started = False
        self._track_memory = track_memory
        self._track_cpu = track_cpu
        self._cpu_start_user: float | None = None
        self._cpu_start_system: float | None = None
        self._wall_start: float | None = None

    def start(self) -> None:
        """Start performance tracking.

        Initializes tracemalloc and resets statistics. Should be called
        once before the operation to be tracked.

        Raises:
            RuntimeError: If tracker is already running.
        """
        if self._started:
            raise RuntimeError("PerformanceTracker is already running")

        if self._track_memory:
            tracemalloc.start()

        if self._track_cpu:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            self._cpu_start_user = usage.ru_utime
            self._cpu_start_system = usage.ru_stime
            self._wall_start = perf_counter()

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

        peak_memory = 0
        if self._track_memory:
            _, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        cpu_seconds: float | None = None
        cpu_user_seconds: float | None = None
        cpu_system_seconds: float | None = None
        cpu_percent_single_core: float | None = None
        cpu_percent_all_cores: float | None = None

        if (
            self._track_cpu
            and self._cpu_start_user is not None
            and self._cpu_start_system is not None
            and self._wall_start is not None
        ):
            usage = resource.getrusage(resource.RUSAGE_SELF)
            cpu_user_seconds = max(0.0, usage.ru_utime - self._cpu_start_user)
            cpu_system_seconds = max(0.0, usage.ru_stime - self._cpu_start_system)
            cpu_seconds = cpu_user_seconds + cpu_system_seconds
            wall_seconds = max(1e-9, perf_counter() - self._wall_start)

            cpu_percent_single_core = (cpu_seconds / wall_seconds) * 100
            cpu_count = max(1, os.cpu_count() or 1)
            cpu_percent_all_cores = cpu_percent_single_core / cpu_count

            self._cpu_start_user = None
            self._cpu_start_system = None
            self._wall_start = None

        self._started = False

        return PerformanceMetrics(
            peak_memory_bytes=peak_memory,
            cpu_seconds=cpu_seconds,
            cpu_user_seconds=cpu_user_seconds,
            cpu_system_seconds=cpu_system_seconds,
            cpu_percent_single_core=cpu_percent_single_core,
            cpu_percent_all_cores=cpu_percent_all_cores,
        )

    def is_active(self) -> bool:
        """Check if tracker is currently active.

        Returns:
            True if tracking is running, False otherwise.
        """
        return self._started
