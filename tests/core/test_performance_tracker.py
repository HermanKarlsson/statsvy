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

    def test_tracker_cpu_only_collects_cpu_metrics(self) -> None:
        """CPU-only tracking should populate CPU fields without memory."""
        tracker = PerformanceTracker(track_memory=False, track_cpu=True)

        with (
            patch("statsvy.core.performance_tracker.resource.getrusage") as mock_usage,
            patch("statsvy.core.performance_tracker.thread_time") as mock_thread_time,
            patch("statsvy.core.performance_tracker.perf_counter") as mock_clock,
        ):
            mock_usage.side_effect = [
                type("Usage", (), {"ru_utime": 1.0, "ru_stime": 0.5})(),
                type("Usage", (), {"ru_utime": 1.6, "ru_stime": 0.9})(),
            ]
            mock_thread_time.side_effect = [30.0, 31.0]
            mock_clock.side_effect = [10.0, 11.0]

            tracker.start()
            metrics = tracker.stop()

            assert metrics.peak_memory_bytes == 0
            assert metrics.cpu_user_seconds == pytest.approx(0.6)
            assert metrics.cpu_system_seconds == pytest.approx(0.4)
            assert metrics.cpu_seconds == pytest.approx(1.0)
            assert metrics.cpu_percent_single_core == pytest.approx(100.0)
            assert metrics.cpu_percent_all_cores is not None

    def test_tracker_memory_and_cpu_collects_both(self) -> None:
        """Combined tracking should collect both peak memory and CPU deltas."""
        tracker = PerformanceTracker(track_memory=True, track_cpu=True)

        with (
            patch("statsvy.core.performance_tracker.tracemalloc") as mock_tm,
            patch("statsvy.core.performance_tracker.resource.getrusage") as mock_usage,
            patch("statsvy.core.performance_tracker.thread_time") as mock_thread_time,
            patch("statsvy.core.performance_tracker.perf_counter") as mock_clock,
        ):
            mock_tm.get_traced_memory.return_value = (1_000, 2_000)
            mock_usage.side_effect = [
                type("Usage", (), {"ru_utime": 2.0, "ru_stime": 1.0})(),
                type("Usage", (), {"ru_utime": 2.2, "ru_stime": 1.1})(),
            ]
            mock_thread_time.side_effect = [40.0, 40.3]
            mock_clock.side_effect = [20.0, 20.5]

            tracker.start()
            metrics = tracker.stop()

            assert metrics.peak_memory_bytes == 2_000
            assert metrics.cpu_seconds == pytest.approx(0.3)
            assert metrics.cpu_percent_single_core == pytest.approx(60.0)
            assert metrics.cpu_percent_all_cores is not None

    def test_tracker_cpu_single_core_percent_is_clamped(self) -> None:
        """Single-core CPU percentage should never exceed 100%."""
        tracker = PerformanceTracker(track_memory=False, track_cpu=True)

        with (
            patch("statsvy.core.performance_tracker.resource.getrusage") as mock_usage,
            patch("statsvy.core.performance_tracker.thread_time") as mock_thread_time,
            patch("statsvy.core.performance_tracker.perf_counter") as mock_clock,
            patch("statsvy.core.performance_tracker.os.cpu_count", return_value=8),
        ):
            mock_usage.side_effect = [
                type("Usage", (), {"ru_utime": 1.0, "ru_stime": 0.0})(),
                type("Usage", (), {"ru_utime": 2.1, "ru_stime": 0.0})(),
            ]
            mock_thread_time.side_effect = [50.0, 51.1]
            mock_clock.side_effect = [10.0, 11.0]

            tracker.start()
            metrics = tracker.stop()

            assert metrics.cpu_seconds == pytest.approx(1.1)
            assert metrics.cpu_percent_single_core == pytest.approx(100.0)
            assert metrics.cpu_percent_all_cores == pytest.approx(13.75)

    def test_tracker_single_core_uses_thread_cpu_time(self) -> None:
        """Single-core CPU% should be derived from current-thread CPU time."""
        tracker = PerformanceTracker(track_memory=False, track_cpu=True)

        with (
            patch("statsvy.core.performance_tracker.resource.getrusage") as mock_usage,
            patch("statsvy.core.performance_tracker.thread_time") as mock_thread_time,
            patch("statsvy.core.performance_tracker.perf_counter") as mock_clock,
            patch("statsvy.core.performance_tracker.os.cpu_count", return_value=4),
        ):
            # Process CPU delta is 1.2 s over 1.0 s wall => 120% process CPU.
            mock_usage.side_effect = [
                type("Usage", (), {"ru_utime": 1.0, "ru_stime": 0.2})(),
                type("Usage", (), {"ru_utime": 2.0, "ru_stime": 0.4})(),
            ]
            # Current thread CPU delta is 0.6 s over 1.0 s wall => 60% single-core.
            mock_thread_time.side_effect = [10.0, 10.6]
            mock_clock.side_effect = [20.0, 21.0]

            tracker.start()
            metrics = tracker.stop()

            assert metrics.cpu_seconds == pytest.approx(1.2)
            assert metrics.cpu_percent_single_core == pytest.approx(60.0)
            assert metrics.cpu_percent_all_cores == pytest.approx(30.0)
