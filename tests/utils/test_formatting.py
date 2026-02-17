"""Unit tests for formatting utilities (parse_size_to_mb)."""

import pytest

from statsvy.utils.formatting import parse_size_to_mb


class TestParseSizeToMb:
    """Unit tests for parse_size_to_mb."""

    def test_parse_mb_without_unit(self) -> None:
        """Numeric input without unit is treated as MB."""
        assert parse_size_to_mb("1") == pytest.approx(1.0)

    def test_parse_mb_with_unit(self) -> None:
        """MB inputs (including decimals) parse correctly."""
        assert parse_size_to_mb("1MB") == pytest.approx(1.0)
        assert parse_size_to_mb("1.5mb") == pytest.approx(1.5)

    def test_parse_kb(self) -> None:
        """KB inputs are converted to MB using 1024 base."""
        assert parse_size_to_mb("1024kb") == pytest.approx(1.0)
        assert parse_size_to_mb("512kb") == pytest.approx(0.5)

    def test_parse_bytes(self) -> None:
        """Byte inputs are converted to MB."""
        assert parse_size_to_mb("1048576b") == pytest.approx(1.0)
        assert parse_size_to_mb("512b") == pytest.approx(512 / 1024 / 1024)

    def test_invalid_values_raise(self) -> None:
        """Invalid strings raise ValueError."""
        with pytest.raises(ValueError):
            parse_size_to_mb("")
        with pytest.raises(ValueError):
            parse_size_to_mb("foo")
