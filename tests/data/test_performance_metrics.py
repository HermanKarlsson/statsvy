"""Unit tests for PerformanceMetrics dataclass and its formatter."""

import pytest

from statsvy.data.performance_metrics import PerformanceMetrics
from statsvy.formatters.performance_metrics_formatter import PerformanceMetricsFormatter


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics data class."""

    def test_performance_metrics_creation(self) -> None:
        """Test creating a PerformanceMetrics instance and defaults for new fields."""
        metrics = PerformanceMetrics(peak_memory_bytes=50_000_000)

        assert metrics.peak_memory_bytes == 50_000_000
        assert metrics.total_bytes_read == 0
        assert metrics.total_io_time_seconds == 0.0
        assert metrics.files_read_count == 0

    def test_peak_memory_mb(self) -> None:
        """Test peak_memory_mb conversion via formatter."""
        metrics = PerformanceMetrics(peak_memory_bytes=52_428_800)  # Exactly 50 MB

        assert PerformanceMetricsFormatter.peak_memory_mb(metrics) == 50.0

    def test_peak_memory_mb_with_rounding(self) -> None:
        """Test peak_memory_mb conversion and rounding via formatter."""
        metrics = PerformanceMetrics(peak_memory_bytes=45_329_555)

        assert PerformanceMetricsFormatter.peak_memory_mb(metrics) == 43.23

    def test_format_text(self) -> None:
        """Test text formatting of metrics via formatter."""
        metrics = PerformanceMetrics(peak_memory_bytes=52_428_800)  # 50 MB

        formatted = PerformanceMetricsFormatter.format_text(metrics)
        assert formatted == "Memory: peak 50 MB"

    def test_format_text_with_decimals(self) -> None:
        """Test text formatting with decimal values via formatter."""
        metrics = PerformanceMetrics(peak_memory_bytes=47_453_132)  # ~45.25 MB

        formatted = PerformanceMetricsFormatter.format_text(metrics)
        assert "Memory: peak" in formatted
        assert "MB" in formatted

    def test_to_dict(self) -> None:
        """Test JSON serialization via formatter to_dict()."""
        metrics = PerformanceMetrics(peak_memory_bytes=52_428_800)

        result = PerformanceMetricsFormatter.to_dict(metrics)

        assert "peak_memory_bytes" in result
        assert "peak_memory_mb" in result
        assert result["peak_memory_bytes"] == 52_428_800
        assert result["peak_memory_mb"] == 50.0

    def test_performance_metrics_is_immutable(self) -> None:
        """Test that PerformanceMetrics is immutable (frozen)."""
        metrics = PerformanceMetrics(peak_memory_bytes=50_000_000)

        with pytest.raises(AttributeError):
            metrics.peak_memory_bytes = 60_000_000  # type: ignore

    def test_performance_metrics_has_slots(self) -> None:
        """Test that PerformanceMetrics uses __slots__ for memory efficiency."""
        # Verify the class has __slots__ defined
        assert hasattr(PerformanceMetrics, "__slots__")
        # Verify the slots contain the expected fields
        slots = PerformanceMetrics.__slots__
        assert "peak_memory_bytes" in slots

    def test_zero_memory_metrics(self) -> None:
        """Test metrics with zero memory values."""
        metrics = PerformanceMetrics(peak_memory_bytes=0)

        assert PerformanceMetricsFormatter.peak_memory_mb(metrics) == 0.0
        assert "0 B" in PerformanceMetricsFormatter.format_text(metrics)

    def test_large_memory_metrics(self) -> None:
        """Test metrics with large memory values."""
        metrics = PerformanceMetrics(peak_memory_bytes=1_073_741_824)  # 1 GB

        assert PerformanceMetricsFormatter.peak_memory_mb(metrics) == 1024.0
