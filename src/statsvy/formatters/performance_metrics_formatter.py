"""Formatting and serialization logic for PerformanceMetrics."""

from typing import Any

from statsvy.data.performance_metrics import PerformanceMetrics
from statsvy.utils.formatting import format_size


class PerformanceMetricsFormatter:
    """Handles formatting and serialization of PerformanceMetrics.

    Separates presentation and serialization logic from the immutable
    PerformanceMetrics dataclass to maintain the data/logic boundary.
    """

    @staticmethod
    def peak_memory_mb(metrics: PerformanceMetrics) -> float:
        """Return peak memory usage in megabytes.

        Args:
            metrics: The PerformanceMetrics instance.

        Returns:
            Peak memory in MB rounded to 2 decimal places.
        """
        return round(metrics.peak_memory_bytes / (1024 * 1024), 2)

    @staticmethod
    def _format_throughput(bytes_per_sec: float | None) -> str:
        """Format throughput bytes/sec using format_size or return 'N/A'."""
        if not bytes_per_sec or bytes_per_sec <= 0:
            return "N/A"
        # Reuse format_size for human-friendly units
        return f"{format_size(int(bytes_per_sec))}/s"

    @staticmethod
    def format_text(metrics: PerformanceMetrics) -> str:
        """Return formatted text representation of performance metrics.

        Shows Memory metrics and, when available, I/O metrics including
        total bytes read, cumulative I/O time and an estimated throughput.

        Args:
            metrics: The PerformanceMetrics instance.

        Returns:
            Human-readable string with performance metrics.
        """
        parts: list[str] = []
        parts.append(f"Memory: peak {format_size(metrics.peak_memory_bytes)}")

        if metrics.total_bytes_read or metrics.total_io_time_seconds:
            throughput = (
                metrics.total_bytes_read / metrics.total_io_time_seconds
                if metrics.total_io_time_seconds > 0
                else None
            )
            parts.append(
                f"I/O: read {format_size(metrics.total_bytes_read)} "
                f"in {metrics.total_io_time_seconds:.2f}s "
                f"({PerformanceMetricsFormatter._format_throughput(throughput)})"
            )

        return " | ".join(parts)

    @staticmethod
    def to_dict(metrics: PerformanceMetrics) -> dict[str, Any]:
        """Return a JSON-serializable representation of metrics.

        Args:
            metrics: The PerformanceMetrics instance.

        Returns:
            Dictionary with performance metric fields for serialization.
        """
        io_throughput = (
            metrics.total_bytes_read / metrics.total_io_time_seconds
            if metrics.total_io_time_seconds > 0
            else None
        )

        return {
            "peak_memory_bytes": metrics.peak_memory_bytes,
            "peak_memory_mb": PerformanceMetricsFormatter.peak_memory_mb(metrics),
            "total_bytes_read": metrics.total_bytes_read,
            "total_io_time_seconds": metrics.total_io_time_seconds,
            "files_read_count": metrics.files_read_count,
            "io_throughput_bps": io_throughput,
        }
