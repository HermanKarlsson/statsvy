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
    def format_text(metrics: PerformanceMetrics) -> str:
        """Return formatted text representation of performance metrics.

        Behavior:
        - I/O-only metrics: show `IO: X.XX MiB/s` (no memory line).
        - Memory-only metrics: show `Memory: peak ...`.
        - Combined metrics: show memory then I/O on separate lines.
        """
        parts: list[str] = []

        # Memory line (only if a non-zero peak was observed)
        if metrics.peak_memory_bytes:
            parts.append(f"Memory: peak {format_size(metrics.peak_memory_bytes)}")

        # I/O line (present when io_mb_s was measured)
        if metrics.io_mb_s is not None:
            parts.append(f"IO: {metrics.io_mb_s:.2f} MiB/s")

        # Fallback to a memory line if nothing else is present
        if not parts:
            return f"Memory: peak {format_size(0)}"

        return "\n".join(parts)

    @staticmethod
    def to_dict(metrics: PerformanceMetrics) -> dict[str, Any]:
        """Return a JSON-serializable representation of metrics.

        Args:
            metrics: The PerformanceMetrics instance.

        Returns:
            Dictionary with performance metric fields for serialization.
        """
        result: dict[str, Any] = {
            "peak_memory_bytes": metrics.peak_memory_bytes,
            "peak_memory_mb": PerformanceMetricsFormatter.peak_memory_mb(metrics),
        }

        # Optional I/O fields
        if metrics.bytes_read:
            result["bytes_read"] = metrics.bytes_read
        if metrics.io_mb_s is not None:
            result["io_mb_s"] = round(metrics.io_mb_s, 2)

        return result
