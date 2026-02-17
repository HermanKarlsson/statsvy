"""Timeout checking utility for scan operations."""

from time import perf_counter
from typing import Self


class TimeoutChecker:
    """Monitors elapsed time and raises TimeoutError when limit exceeded.

    This class provides a context manager for tracking operation duration
    and enforcing timeout limits in long-running operations like scanning
    and analysis.

    Attributes:
        timeout_seconds: Maximum allowed duration in seconds (int or float).
        start_time: Time when checking started (set by start()).
    """

    def __init__(self, timeout_seconds: int | float) -> None:
        """Initialize timeout checker.

        Args:
            timeout_seconds: Maximum allowed duration in seconds.
                Must be non-negative. Use 0 to disable timeout checking.
                Can be a float for sub-second timeouts.

        Raises:
            ValueError: If timeout_seconds is negative.
        """
        if timeout_seconds < 0:
            raise ValueError(
                f"timeout_seconds must be non-negative, got {timeout_seconds}"
            )
        self.timeout_seconds = timeout_seconds
        self.start_time: float | None = None

    def __enter__(self) -> Self:
        """Start timing when entering context."""
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context (no cleanup needed)."""
        pass

    def start(self) -> None:
        """Start the timeout timer."""
        self.start_time = perf_counter()

    def check(self, context: str = "operation") -> None:
        """Check if timeout has been exceeded.

        Args:
            context: Description of current operation for error message.

        Raises:
            TimeoutError: If elapsed time exceeds timeout limit.
            RuntimeError: If called before start().
        """
        if self.start_time is None:
            raise RuntimeError("TimeoutChecker.start() must be called before check()")

        if self.timeout_seconds == 0:
            return  # Timeout disabled

        elapsed = perf_counter() - self.start_time
        if elapsed > self.timeout_seconds:
            raise TimeoutError(
                f"Scan exceeded {self.timeout_seconds}s timeout limit during "
                f"{context} (elapsed: {elapsed:.1f}s)"
            )

    def elapsed(self) -> float:
        """Get elapsed time since start.

        Returns:
            Elapsed time in seconds.

        Raises:
            RuntimeError: If called before start().
        """
        if self.start_time is None:
            raise RuntimeError("TimeoutChecker.start() must be called before elapsed()")
        return perf_counter() - self.start_time
