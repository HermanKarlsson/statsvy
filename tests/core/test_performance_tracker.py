"""Unit tests for PerformanceTracker class."""

from unittest.mock import patch

import pytest

from statsvy.core.performance_tracker import PerformanceTracker
from statsvy.data.performance_metrics import PerformanceMetrics


class TestPerformanceTracker:
    """Tests for PerformanceTracker class."""

    def test_tracker_initialization(self) -> None:
        """Test tracker initializes in inactive state."""
        tracker = PerformanceTracker()

        assert not tracker.is_active()

    def test_tracker_start(self) -> None:
        """Test tracker starts successfully."""
        tracker = PerformanceTracker()

        with patch("statsvy.core.performance_tracker.tracemalloc") as mock_tm:
            tracker.start()

            mock_tm.start.assert_called_once()
            assert tracker.is_active()

    def test_tracker_stop_returns_metrics(self) -> None:
        """Test tracker stops and returns PerformanceMetrics."""
        tracker = PerformanceTracker()

        with patch("statsvy.core.performance_tracker.tracemalloc") as mock_tm:
            mock_tm.get_traced_memory.return_value = (12_000_000, 50_000_000)

            tracker.start()
            metrics = tracker.stop()

            assert isinstance(metrics, PerformanceMetrics)
            assert metrics.peak_memory_bytes == 50_000_000
            assert not tracker.is_active()
            mock_tm.stop.assert_called_once()

    def test_tracker_cannot_start_twice(self) -> None:
        """Test tracker raises error if started twice."""
        tracker = PerformanceTracker()

        with patch("statsvy.core.performance_tracker.tracemalloc"):
            tracker.start()

            with pytest.raises(RuntimeError, match="already running"):
                tracker.start()

    def test_tracker_cannot_stop_without_starting(self) -> None:
        """Test tracker raises error if stopped without being started."""
        tracker = PerformanceTracker()

        with pytest.raises(RuntimeError, match="has not been started"):
            tracker.stop()

    def test_tracker_can_restart_after_stop(self) -> None:
        """Test tracker can be restarted after stopping."""
        tracker = PerformanceTracker()

        with patch("statsvy.core.performance_tracker.tracemalloc") as mock_tm:
            mock_tm.get_traced_memory.return_value = (10_000_000, 40_000_000)

            # First cycle
            tracker.start()
            assert tracker.is_active()
            metrics1 = tracker.stop()
            assert not tracker.is_active()
            assert metrics1.peak_memory_bytes == 40_000_000

            # Second cycle
            mock_tm.get_traced_memory.return_value = (20_000_000, 50_000_000)
            tracker.start()
            assert tracker.is_active()
            metrics2 = tracker.stop()
            assert not tracker.is_active()
            assert metrics2.peak_memory_bytes == 50_000_000

    def test_tracker_stop_resets_active_flag(self) -> None:
        """Test that stop() properly resets the active flag."""
        tracker = PerformanceTracker()

        with patch("statsvy.core.performance_tracker.tracemalloc") as mock_tm:
            mock_tm.get_traced_memory.return_value = (10_000_000, 40_000_000)

            tracker.start()
            assert tracker.is_active()

            tracker.stop()
            assert not tracker.is_active()

    def test_tracker_with_real_tracemalloc(self) -> None:
        """Integration test with real tracemalloc (basic memory allocation)."""
        tracker = PerformanceTracker()

        tracker.start()

        # Allocate some memory
        _data = [i for i in range(100_000)]

        metrics = tracker.stop()

        # Verify we got valid metrics back
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.peak_memory_bytes > 0

    def test_tracker_is_context_free(self) -> None:
        """Test tracker can be used without context manager pattern."""
        tracker = PerformanceTracker()

        with patch("statsvy.core.performance_tracker.tracemalloc") as mock_tm:
            mock_tm.get_traced_memory.return_value = (15_000_000, 45_000_000)

            # Should work without context manager
            tracker.start()
            metrics = tracker.stop()

            assert isinstance(metrics, PerformanceMetrics)
            assert not tracker.is_active()

    def test_record_io_accumulates_counters(self) -> None:
        """record_io should accumulate bytes, time and file count when enabled."""
        tracker = PerformanceTracker(track_memory=False, track_io=True)

        tracker.start()
        tracker.record_io(1024, 0.01)
        tracker.record_io(2048, 0.02)
        metrics = tracker.stop()

        assert metrics.total_bytes_read == 3072
        assert metrics.files_read_count == 2
        assert metrics.total_io_time_seconds >= 0.03

    def test_is_tracking_io_flag(self) -> None:
        """is_tracking_io() reflects constructor flag."""
        t1 = PerformanceTracker(track_memory=True, track_io=False)
        assert not t1.is_tracking_io()

        t2 = PerformanceTracker(track_memory=False, track_io=True)
        assert t2.is_tracking_io()
