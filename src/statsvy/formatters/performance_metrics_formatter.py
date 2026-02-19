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

        Uses the shared ``format_size`` utility so memory is displayed using
        the same adaptive units as other size outputs.

        Args:
            metrics: The PerformanceMetrics instance.

        Returns:
            Human-readable string with peak memory usage.
        """
        return f"Memory: peak {format_size(metrics.peak_memory_bytes)}"

    @staticmethod
    def to_dict(metrics: PerformanceMetrics) -> dict[str, Any]:
        """Return a JSON-serializable representation of metrics.

        Args:
            metrics: The PerformanceMetrics instance.

        Returns:
            Dictionary with performance metric fields for serialization.
        """
        return {
            "peak_memory_bytes": metrics.peak_memory_bytes,
            "peak_memory_mb": PerformanceMetricsFormatter.peak_memory_mb(metrics),
        }
