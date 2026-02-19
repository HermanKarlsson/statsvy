"""Performance tracking for scan operations.

This module provides a PerformanceTracker class that measures and collects
performance metrics during scan operations. Currently tracks memory usage
via tracemalloc; designed to be extended with additional metrics.
"""

import tracemalloc

from statsvy.data.performance_metrics import PerformanceMetrics


class PerformanceTracker:
    """Tracks performance metrics during scan operations.

    Supports both memory tracking (via tracemalloc) and lightweight
    application-level I/O accounting (bytes/time/files). The tracker is
    intentionally cheap for I/O accounting so the measurement overhead is
    minimal when enabled.
    """

    def __init__(self, track_memory: bool = True, track_io: bool = False) -> None:
        """Initialize the performance tracker.

        Args:
            track_memory: Whether to enable tracemalloc-based memory tracking.
                Defaults to True for backward compatibility.
            track_io: Whether to enable application-level I/O accounting.
                Defaults to False.
        """
        self._started = False
        self._track_memory = track_memory
        self._track_io = track_io

        # I/O counters
        self._total_bytes_read: int = 0
        self._total_io_time_seconds: float = 0.0
        self._files_read_count: int = 0

    def start(self) -> None:
        """Start performance tracking.

        Initializes tracemalloc only when memory tracking was requested.

        Raises:
            RuntimeError: If tracker is already running.
        """
        if self._started:
            raise RuntimeError("PerformanceTracker is already running")

        if self._track_memory:
            tracemalloc.start()
        self._started = True

    def record_io(
        self, bytes_read: int, elapsed_seconds: float, path: str | None = None
    ) -> None:
        """Record a single application-level I/O operation.

        This method is intentionally minimal: it performs a few arithmetic
        updates and returns quickly. It is a no-op if the tracker is not
        active or I/O accounting was not enabled.

        Args:
            bytes_read: Number of bytes read by the operation.
            elapsed_seconds: Wall-clock time spent performing the operation.
            path: Optional path (string) for diagnostic purposes. Not stored.
        """
        # Fast-path: only update counters when tracker started and I/O enabled
        if not self._started or not self._track_io:
            return

        if bytes_read:
            self._total_bytes_read += int(bytes_read)
        if elapsed_seconds:
            self._total_io_time_seconds += float(elapsed_seconds)
        self._files_read_count += 1

        # Preserve API surface for callers that pass a path (avoid unused-arg)
        if path is not None:
            _ = path  # intentionally not stored; used only for diagnostics

    def is_tracking_io(self) -> bool:
        """Return True when I/O accounting is enabled for this tracker."""
        return self._track_io

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

        self._started = False

        return PerformanceMetrics(
            peak_memory_bytes=peak_memory,
            total_bytes_read=self._total_bytes_read,
            total_io_time_seconds=self._total_io_time_seconds,
            files_read_count=self._files_read_count,
        )

    def is_active(self) -> bool:
        """Check if tracker is currently active.

        Returns:
            True if tracking is running, False otherwise.
        """
        return self._started
