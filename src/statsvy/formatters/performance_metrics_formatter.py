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
        - CPU-only metrics: show CPU time and CPU percentages.
        - Combined metrics: show each available metric on separate lines.
        """
        parts: list[str] = []

        # Memory line (only if a non-zero peak was observed)
        if metrics.peak_memory_bytes:
            parts.append(f"Memory: peak {format_size(metrics.peak_memory_bytes)}")

        # I/O line (present when io_mb_s was measured)
        if metrics.io_mb_s is not None:
            parts.append(f"IO: {metrics.io_mb_s:.2f} MiB/s")

        # CPU lines
        if metrics.cpu_seconds is not None:
            parts.append(f"CPU: {metrics.cpu_seconds:.4f} s")
        if metrics.cpu_percent_single_core is not None:
            parts.append(f"CPU% (single-core): {metrics.cpu_percent_single_core:.2f}%")
        if metrics.cpu_percent_all_cores is not None:
            parts.append(f"CPU% (all-cores): {metrics.cpu_percent_all_cores:.2f}%")

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

        PerformanceMetricsFormatter._add_io_fields(result, metrics)
        PerformanceMetricsFormatter._add_cpu_fields(result, metrics)

        return result

    @staticmethod
    def _add_io_fields(result: dict[str, Any], metrics: PerformanceMetrics) -> None:
        """Add optional I/O fields to serialized metrics."""
        if metrics.bytes_read:
            result["bytes_read"] = metrics.bytes_read
        if metrics.io_mb_s is not None:
            result["io_mb_s"] = round(metrics.io_mb_s, 2)

    @staticmethod
    def _add_cpu_fields(result: dict[str, Any], metrics: PerformanceMetrics) -> None:
        """Add optional CPU fields to serialized metrics."""
        cpu_numeric_fields = (
            ("cpu_seconds", metrics.cpu_seconds, 6),
            ("cpu_user_seconds", metrics.cpu_user_seconds, 6),
            ("cpu_system_seconds", metrics.cpu_system_seconds, 6),
            ("cpu_percent_single_core", metrics.cpu_percent_single_core, 2),
            ("cpu_percent_all_cores", metrics.cpu_percent_all_cores, 2),
        )
        for key, value, precision in cpu_numeric_fields:
            if value is not None:
                result[key] = round(value, precision)
