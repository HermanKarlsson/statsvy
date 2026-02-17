"""Tests for TimeoutChecker utility class."""

import time

import pytest

from statsvy.utils.timeout_checker import TimeoutChecker


class TestTimeoutCheckerInit:
    """Tests for TimeoutChecker initialization."""

    def test_init_with_positive_timeout(self) -> None:
        """TimeoutChecker should accept positive timeout values."""
        checker = TimeoutChecker(300)
        assert checker.timeout_seconds == 300
        assert checker.start_time is None

    def test_init_with_zero_timeout(self) -> None:
        """TimeoutChecker should accept zero (disabled timeout)."""
        checker = TimeoutChecker(0)
        assert checker.timeout_seconds == 0

    def test_init_with_negative_timeout_raises_error(self) -> None:
        """TimeoutChecker should reject negative timeout values."""
        with pytest.raises(ValueError, match="must be non-negative"):
            TimeoutChecker(-1)


class TestTimeoutCheckerStart:
    """Tests for TimeoutChecker.start() method."""

    def test_start_sets_start_time(self) -> None:
        """start() should set the start_time attribute."""
        checker = TimeoutChecker(300)
        assert checker.start_time is None
        checker.start()
        assert checker.start_time is not None
        assert isinstance(checker.start_time, float)

    def test_start_can_be_called_multiple_times(self) -> None:
        """start() can be called multiple times to reset timer."""
        checker = TimeoutChecker(300)
        checker.start()
        first_start = checker.start_time
        time.sleep(0.01)
        checker.start()
        second_start = checker.start_time
        assert second_start > first_start  # type: ignore[operator]


class TestTimeoutCheckerContextManager:
    """Tests for TimeoutChecker as context manager."""

    def test_enter_starts_timer(self) -> None:
        """Entering context should start the timer."""
        checker = TimeoutChecker(300)
        assert checker.start_time is None
        with checker:
            assert checker.start_time is not None

    def test_exit_does_not_clear_timer(self) -> None:
        """Exiting context keeps the timer for inspection."""
        checker = TimeoutChecker(300)
        with checker:
            pass
        assert checker.start_time is not None


class TestTimeoutCheckerCheck:
    """Tests for TimeoutChecker.check() method."""

    def test_check_before_start_raises_error(self) -> None:
        """check() should raise RuntimeError if called before start()."""
        checker = TimeoutChecker(300)
        with pytest.raises(RuntimeError, match="must be called before check"):
            checker.check()

    def test_check_within_timeout_does_not_raise(self) -> None:
        """check() should not raise if within timeout limit."""
        checker = TimeoutChecker(10)
        checker.start()
        checker.check("test operation")  # Should not raise

    def test_check_with_zero_timeout_never_raises(self) -> None:
        """check() should never raise when timeout is disabled (0)."""
        checker = TimeoutChecker(0)
        checker.start()
        time.sleep(0.01)
        checker.check("test operation")  # Should not raise

    def test_check_after_timeout_raises_timeout_error(self) -> None:
        """check() should raise TimeoutError when timeout exceeded."""
        checker = TimeoutChecker(0.01)  # 10ms timeout
        checker.start()
        time.sleep(0.02)  # Wait longer than timeout
        with pytest.raises(
            TimeoutError,
            match=r"exceeded 0\.01s timeout limit during test operation",
        ):
            checker.check("test operation")

    def test_check_includes_context_in_error_message(self) -> None:
        """TimeoutError should include context in message."""
        checker = TimeoutChecker(0.01)
        checker.start()
        time.sleep(0.02)
        with pytest.raises(TimeoutError, match="file analysis"):
            checker.check("file analysis")

    def test_check_includes_elapsed_time_in_error_message(self) -> None:
        """TimeoutError should include elapsed time in message."""
        checker = TimeoutChecker(0.01)
        checker.start()
        time.sleep(0.02)
        with pytest.raises(TimeoutError, match=r"elapsed: \d+\.\d+s"):
            checker.check("test")

    def test_check_default_context(self) -> None:
        """check() should use default context if not provided."""
        checker = TimeoutChecker(0.01)
        checker.start()
        time.sleep(0.02)
        with pytest.raises(TimeoutError, match="operation"):
            checker.check()


class TestTimeoutCheckerElapsed:
    """Tests for TimeoutChecker.elapsed() method."""

    def test_elapsed_before_start_raises_error(self) -> None:
        """elapsed() should raise RuntimeError if called before start()."""
        checker = TimeoutChecker(300)
        with pytest.raises(RuntimeError, match="must be called before elapsed"):
            checker.elapsed()

    def test_elapsed_returns_time_since_start(self) -> None:
        """elapsed() should return time since start() was called."""
        checker = TimeoutChecker(300)
        checker.start()
        time.sleep(0.01)
        elapsed = checker.elapsed()
        assert elapsed >= 0.01
        assert elapsed < 1.0  # Should be very small

    def test_elapsed_increases_over_time(self) -> None:
        """elapsed() should increase as time passes."""
        checker = TimeoutChecker(300)
        checker.start()
        first_elapsed = checker.elapsed()
        time.sleep(0.01)
        second_elapsed = checker.elapsed()
        assert second_elapsed > first_elapsed


class TestTimeoutCheckerIntegration:
    """Integration tests for typical TimeoutChecker usage patterns."""

    def test_typical_usage_with_context_manager(self) -> None:
        """Test typical usage pattern with context manager."""
        checker = TimeoutChecker(10)
        with checker:
            for _ in range(5):
                checker.check("iteration")
                time.sleep(0.001)
        # Should complete without timeout

    def test_manual_start_and_check(self) -> None:
        """Test manual start and check pattern."""
        checker = TimeoutChecker(10)
        checker.start()
        for _ in range(5):
            checker.check("processing")
            time.sleep(0.001)
        # Should complete without timeout

    def test_timeout_during_loop(self) -> None:
        """Test that timeout is detected during loop iteration."""
        checker = TimeoutChecker(0.02)  # 20ms timeout
        checker.start()
        iteration_count = 0
        with pytest.raises(TimeoutError):
            for i in range(100):
                time.sleep(0.005)  # 5ms per iteration
                checker.check(f"iteration {i}")
                iteration_count = i
        # Should have completed some iterations before timeout
        assert iteration_count > 0
        assert iteration_count < 100
